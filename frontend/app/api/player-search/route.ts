import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const apiUrl = process.env.FANTASY_API_URL;
  const apiKey = process.env.FANTASY_API_KEY;

  if (!apiUrl || !apiKey) {
    return NextResponse.json(
      {
        error: "Fantasy API configuration is missing.",
      },
      {
        status: 500,
      }
    );
  }

  const body = await request.json();

  const response = await fetch(
    `${apiUrl}/tools/search-players`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    }
  );

  const data = await response.json();

  return NextResponse.json(data, {
    status: response.status,
  });
}