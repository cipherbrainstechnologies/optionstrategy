import { NextResponse } from 'next/server'

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export async function GET() {
  try {
    const r = await fetch(`${API}/fyers/auth-url`, { cache: 'no-store' })
    const data = await r.json()
    return NextResponse.json(data, { status: r.status })
  } catch (error) {
    return NextResponse.json(
      { 
        success: false, 
        auth_url: null, 
        message: `Error fetching auth URL: ${error instanceof Error ? error.message : 'Unknown error'}` 
      }, 
      { status: 500 }
    )
  }
}
