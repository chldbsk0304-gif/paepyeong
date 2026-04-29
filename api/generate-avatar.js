export const config = {
  api: { bodyParser: { sizeLimit: '20mb' } },
  maxDuration: 60,
};

const MODEL = 'gemini-3.1-flash-image-preview';
const GEMINI_URL = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`;

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method Not Allowed' });

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'GEMINI_API_KEY가 설정되지 않았습니다' });

  const { avatarBase64, avatarMimeType, clothingUrls, bodyData } = req.body;

  if (!avatarBase64) return res.status(400).json({ error: 'avatarBase64가 필요합니다' });
  if (!clothingUrls?.length) return res.status(400).json({ error: 'clothingUrls가 필요합니다' });
  if (!bodyData) return res.status(400).json({ error: 'bodyData가 필요합니다' });

  // ── 의류 이미지 URL → base64 변환 (서버사이드 fetch로 CORS 우회) ──
  let clothingImages;
  try {
    clothingImages = await Promise.all(
      clothingUrls.map(async (url) => {
        const resp = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
        if (!resp.ok) throw new Error(`의류 이미지 로드 실패 (${resp.status}): ${url}`);
        const buffer = await resp.arrayBuffer();
        const base64 = Buffer.from(buffer).toString('base64');
        const ct = resp.headers.get('content-type') || 'image/jpeg';
        return { data: base64, mimeType: ct.split(';')[0] };
      })
    );
  } catch (e) {
    return res.status(502).json({ error: `의류 이미지 로드 중 오류: ${e.message}` });
  }

  // ── 신체 조건 문자열 ──
  const bodyCondition =
    `Character body specifications: Height ${bodyData.height}, Weight ${bodyData.weight}. ` +
    `Body type: ${bodyData.body}. Skin tone: ${bodyData.skin}. Hair: ${bodyData.hair}.`;

  // ── 프롬프트 (사용자 스펙 그대로) ──
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
    `to her body as a single complete outfit — not individually, but all together ` +
    `as one finished coordinated look. Standing in a formal symmetrical attention ` +
    `stance: feet together toes touching, body perfectly upright facing directly ` +
    `forward, both arms straight down at her sides with hands lightly closed ` +
    `against her thighs. Shot from head to toe, full body in frame, no cropping. ` +
    `Professional studio lighting, sharp focus throughout, neutral light grey ` +
    `background. Vertical 9:16 portrait orientation.`;

  // ── Gemini API 호출 ──
  const parts = [
    { inlineData: { mimeType: avatarMimeType || 'image/png', data: avatarBase64 } },
    ...clothingImages.map(img => ({ inlineData: { mimeType: img.mimeType, data: img.data } })),
    { text: promptText },
  ];

  let geminiResp;
  try {
    geminiResp = await fetch(`${GEMINI_URL}?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ role: 'user', parts }],
        generationConfig: { responseModalities: ['TEXT', 'IMAGE'] },
      }),
    });
  } catch (e) {
    return res.status(502).json({ error: `Gemini API 네트워크 오류: ${e.message}` });
  }

  if (!geminiResp.ok) {
    const errText = await geminiResp.text().catch(() => '(응답 읽기 실패)');
    return res.status(geminiResp.status).json({
      error: `Gemini API 오류 (${geminiResp.status})`,
      detail: errText.slice(0, 500),
    });
  }

  let data;
  try {
    data = await geminiResp.json();
  } catch (e) {
    return res.status(500).json({ error: 'Gemini API 응답 파싱 실패' });
  }

  const imagePart = data.candidates?.[0]?.content?.parts?.find(p => p.inlineData?.data);
  if (!imagePart) {
    return res.status(500).json({
      error: '이미지 생성 실패: 응답에 이미지가 없습니다',
      finishReason: data.candidates?.[0]?.finishReason,
      promptFeedback: data.promptFeedback,
    });
  }

  return res.status(200).json({
    imageBase64: imagePart.inlineData.data,
    mimeType: imagePart.inlineData.mimeType || 'image/png',
  });
}
