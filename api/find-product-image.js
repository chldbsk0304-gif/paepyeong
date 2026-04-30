// Vercel serverless: Claude web_search로 패션 제품 공식 이미지 URL 찾기
//
// 입력: { brand, name, category }
// 출력: { imageUrl, source, confidence: 'high'|'medium'|'low' } | { imageUrl: null }

export default async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(204).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'ANTHROPIC_API_KEY not configured' });
  }

  const { brand = '', name = '', category = '' } = req.body || {};
  if (!brand && !name) {
    return res.status(200).json({ imageUrl: null });
  }

  const query = [brand, name, 'official product image'].filter(Boolean).join(' ');
  const userPrompt =
    `다음 패션 제품의 공식 제품 이미지(상품 컷) 직링크 URL 1개를 web_search로 찾아주세요.\n` +
    `브랜드: ${brand || '(미상)'}\n` +
    `제품명: ${name || '(미상)'}\n` +
    `카테고리: ${category || '(미상)'}\n\n` +
    `검색 가이드: "${query}", 무신사·공식몰·패션 커머스 우선.\n` +
    `반드시 최종 응답은 아래 JSON만 출력 (코드블록·해설 금지):\n` +
    `{"imageUrl":"<.jpg|.png|.webp 직링크 또는 null>","source":"<도메인>","confidence":"high|medium|low"}\n` +
    `- 정확한 제품 이미지를 찾으면 confidence "high"\n` +
    `- 비슷한 제품 이미지면 "medium"\n` +
    `- 카테고리 일반 이미지밖에 없으면 "low"\n` +
    `- 신뢰할 만한 이미지가 없으면 imageUrl을 null로`;

  let anthropicResp;
  try {
    anthropicResp = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-6',
        max_tokens: 1024,
        messages: [{ role: 'user', content: userPrompt }],
        tools: [{ type: 'web_search_20250305', name: 'web_search', max_uses: 3 }],
      }),
    });
  } catch (e) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(502).json({ imageUrl: null, error: 'upstream_fetch_failed' });
  }

  const data = await anthropicResp.json();
  res.setHeader('Access-Control-Allow-Origin', '*');

  if (!anthropicResp.ok) {
    return res.status(200).json({ imageUrl: null, error: data?.error?.message || 'upstream_error' });
  }

  // 응답에서 마지막 text 블록을 뽑아 JSON 파싱
  const blocks = Array.isArray(data?.content) ? data.content : [];
  const textBlocks = blocks.filter(b => b?.type === 'text' && typeof b.text === 'string');
  const lastText = textBlocks.length ? textBlocks[textBlocks.length - 1].text : '';
  const m = lastText.match(/\{[\s\S]*\}/);
  if (!m) return res.status(200).json({ imageUrl: null });

  let parsed;
  try { parsed = JSON.parse(m[0]); }
  catch (_) { return res.status(200).json({ imageUrl: null }); }

  const url = parsed?.imageUrl;
  // 직링크 검증 (이미지 확장자 또는 known CDN 패턴)
  const isImg = typeof url === 'string' &&
    /^https?:\/\//i.test(url) &&
    (/\.(jpe?g|png|webp|gif|avif)(\?|$)/i.test(url) || /image|img|cdn|cloudfront|static/i.test(url));

  return res.status(200).json({
    imageUrl: isImg ? url : null,
    source: typeof parsed?.source === 'string' ? parsed.source : null,
    confidence: ['high', 'medium', 'low'].includes(parsed?.confidence) ? parsed.confidence : 'low',
  });
}
