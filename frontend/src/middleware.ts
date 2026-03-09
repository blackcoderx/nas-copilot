import { defineMiddleware } from 'astro:middleware';

const PUBLIC = ['/', '/login'];

export const onRequest = defineMiddleware(({ url, cookies, redirect }, next) => {
  const path  = url.pathname;
  const token = cookies.get('nas_token')?.value;
  const role  = cookies.get('nas_role')?.value ?? 'emt';

  // Redirect authenticated users away from public pages
  if (PUBLIC.includes(path) && token) {
    if (role === 'superadmin') return redirect('/superadmin');
    if (role === 'admin')      return redirect('/admin');
    return redirect('/dashboard');
  }

  // Superadmin-only zone
  if (path.startsWith('/superadmin')) {
    if (!token) return redirect('/login');
    if (role !== 'superadmin') return redirect('/dashboard');
  }

  // Admin-only zone (superadmin can also enter)
  if (path.startsWith('/admin')) {
    if (!token) return redirect('/login');
    if (role !== 'admin' && role !== 'superadmin') return redirect('/dashboard');
  }

  // EMT-protected pages
  const emtProtected = ['/dashboard', '/cases'];
  if (emtProtected.some(p => path === p || path.startsWith(p + '/')) && !token) {
    return redirect('/login');
  }

  return next();
});
