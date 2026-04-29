export const config = {
  api: { bodyParser: { sizeLimit: '20mb' } },
  maxDuration: 60,
};

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method Not Allowed' });

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'GEMINI_API_KEY not configured' });

  const { avatarBase64, avatarMimeType, clothingUrls, bodyData } = req.body;
  if (!avatarBase64 || !clothingUrls?.length || !bodyData) {
    return res.status(400).json({ error: 'avatarBase64, clothingUrls, bodyData are required' });
  }

  // 의류 이미지 URL → base64 변환
  const clothingImages = await Promise.all(
    clothingUrls.map(async (url) => {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`이미지 로드 실패: ${url}`);
      const buffer = await resp.arrayBuffer();
      const base64 = Buffer.from(buffer).toString('base64');
      const ct = resp.headers.get('content-type') || 'image/jpeg';
      return { data: base64, mimeType: ct.split(';')[0] };
    })
  );

  // 신체 조건 문자열 조합
  const bodyCondition =
    `Character body specifications: Height ${bodyData.height}, Weight ${bodyData.weight}. ` +
    `Body type: ${bodyData.body}. Skin tone: ${bodyData.skin}. Hair: ${bodyData.hair}.`;

  const promptText =
    `Use the provided reference images as follows:\n` +
    `Character reference: Match the facial features, hair style, body proportions, ` +
    `and overall appearance of the avatar image as closely as possible.\n` +
    `${bodyCondition}\n` +
    `Outfit reference: Dress the character in the exact clothing items shown in ` +
    `the product images — replicate the design, color, fabric texture, fit, and ` +
    `details (stitching, logos, patterns, silhouette) as accurately as possible ` +
    `for each item (top, bottom, shoes, etc.).\n` +
    `The character should be wearing all provided clothing items naturally fitted ` +
    `to her body. Standing in a formal symmetrical attention stance: feet together ` +
    `toes touching, body perfectly upright facing directly forward, both arms ` +
    `straight down at her sides with hands lightly closed against her thighs.\n` +
    `Shot from head to toe, full body in frame, no cropping. Professional studio ` +
    `lighting, sharp focus throughout, neutral light grey background.\n` +
    `Vertical 9:16 portrait orientation.`;

  const parts = [
    { inlineData: { mimeType: avatarMimeType || 'image/png', data: avatarBase64 } },
    ...clothingImages.map(img => ({ inlineData: { mimeType: img.mimeType, data: img.data } })),
    { text: promptText },
  ];

  const geminiResp = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key=${apiKey}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts }],
        generationConfig: { responseModalities: ['IMAGE'] },
      }),
    }
  );

  if (!geminiResp.ok) {
    const errText = await geminiResp.text();
    return res.status(geminiResp.status).json({ error: `Gemini API 오류 (${geminiResp.status}): ${errText}` });
  }

  const data = await geminiResp.json();
  const imagePart = data.candidates?.[0]?.content?.parts?.find(p => p.inlineData);

  if (!imagePart) {
    return res.status(500).json({ error: '이미지 생성 실패: 응답에 이미지가 없습니다', raw: data });
  }

  return res.status(200).json({
    imageBase64: imagePart.inlineData.data,
    mimeType: imagePart.inlineData.mimeType || 'image/png',
  });
}
