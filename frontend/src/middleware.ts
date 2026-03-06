import { defineMiddleware } from 'astro:middleware';

const PROTECTED = ['/dashboard', '/cases'];
const PUBLIC    = ['/', '/login'];

export const onRequest = defineMiddleware(({ url, cookies, redirect }, next) => {
  const path = url.pathname;
  const token = cookies.get('nas_token')?.value;

  const isProtected = PROTECTED.some(p => path === p || path.startsWith(p + '/'));

  if (isProtected && !token) {
    return redirect('/login');
  }

  if (PUBLIC.includes(path) && token) {
    return redirect('/dashboard');
  }

  return next();
});
