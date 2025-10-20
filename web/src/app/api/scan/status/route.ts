import { NextResponse } from 'next/server'

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export async function GET() {
  const r = await fetch(`${API}/scan/status`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  })
  const data = await r.json()
  return NextResponse.json(data, { status: r.status })
}
