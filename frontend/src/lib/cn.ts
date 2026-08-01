/**
 * Minimal className joiner — no clsx/tailwind-merge dependency yet.
 * Filters out falsy values, joins the rest with spaces.
 */
export function cn(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}
