import { NextResponse } from 'next/server'

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export async function GET() {
  const r = await fetch(`${API}/positions`, { cache: 'no-store' })
  const data = await r.json()
  return NextResponse.json(data, { status: r.status })
}
