import { NextRequest, NextResponse } from "next/server";
import { jwtVerify, errors as joseErrors } from "jose";
import { isPublicPath } from "@/lib/auth";

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET_KEY ?? "dev-secret",
);

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  const token = request.cookies.get("access_token")?.value;
  if (!token) {
    return NextResponse.redirect(new URL("/signin", request.url));
  }

  try {
    await jwtVerify(token, JWT_SECRET, { algorithms: ["HS256"] });
    return NextResponse.next();
  } catch (err) {
    if (err instanceof joseErrors.JWTExpired) {
      return NextResponse.redirect(new URL("/signin", request.url));
    }
    return NextResponse.redirect(new URL("/signin", request.url));
  }
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|health).*)"],
};
