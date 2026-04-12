import { NextRequest } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { SYSTEM_PROMPT, rootCausePrompt } from '@/prompts/root-cause'
import { LLM_MODEL_CHAT, LLM_MAX_TOKENS_CHAT } from '@/lib/constants'

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

export async function POST(req: NextRequest) {
  const { projectContext, question } = await req.json()

  if (!projectContext || !question) {
    return new Response('Missing projectContext or question', { status: 400 })
  }

  const prompt = rootCausePrompt(projectContext, question)

  const stream = await client.messages.stream({
    model: LLM_MODEL_CHAT,
    max_tokens: LLM_MAX_TOKENS_CHAT,
    system: SYSTEM_PROMPT,
    messages: [{ role: 'user', content: prompt }],
  })

  const encoder = new TextEncoder()
  const readable = new ReadableStream({
    async start(controller) {
      for await (const chunk of stream) {
        if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
          controller.enqueue(encoder.encode(chunk.delta.text))
        }
      }
      controller.close()
    },
  })

  return new Response(readable, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Transfer-Encoding': 'chunked',
    },
  })
}
