import { NextResponse } from 'next/server'

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const r = await fetch(`${API}/trading-mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    const data = await r.json()
    return NextResponse.json(data, { status: r.status })
  } catch (error) {
    return NextResponse.json(
      { 
        success: false, 
        message: `Error updating trading mode: ${error instanceof Error ? error.message : 'Unknown error'}` 
      }, 
      { status: 500 }
    )
  }
}
