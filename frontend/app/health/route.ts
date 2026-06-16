const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8001";

export async function GET() {
  try {
    const upstream = await fetch(`${BACKEND_URL}/health`, {
      cache: "no-store",
    });
    const body = await upstream.json();
    return Response.json({ frontend: "ok", backend: body }, { status: 200 });
  } catch (error) {
    return Response.json(
      { frontend: "ok", backend: "unreachable", error: String(error) },
      { status: 502 },
    );
  }
}
