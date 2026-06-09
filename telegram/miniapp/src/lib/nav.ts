/**
 * Helper to build router `to=` values that preserve the current URL's search
 * string (so merchant_id, dev, and friends survive navigation).
 */
export function withSearch(pathname: string): { pathname: string; search: string } {
  return { pathname, search: window.location.search };
}
