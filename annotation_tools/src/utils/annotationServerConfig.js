// Annotation server configuration utility
// Annotation server runs on a fixed port (default: 3001)
// Can be overridden via environment variable VITE_ANNOTATION_SERVER_PORT

const DEFAULT_ANNOTATION_SERVER_PORT = 3001;

/**
 * Gets the annotation server URL
 * Priority:
 * 1. Environment variable VITE_ANNOTATION_SERVER_URL (if set, full URL)
 * 2. Environment variable VITE_ANNOTATION_SERVER_PORT (if set, uses http://localhost:{port})
 * 3. Default port 3001
 */
export function getAnnotationServerUrl() {
  // Check environment variable first (for build-time configuration)
  if (import.meta.env.VITE_ANNOTATION_SERVER_URL) {
    return import.meta.env.VITE_ANNOTATION_SERVER_URL;
  }

  if (import.meta.env.VITE_ANNOTATION_SERVER_PORT) {
    const port = parseInt(import.meta.env.VITE_ANNOTATION_SERVER_PORT, 10);
    if (port > 0 && port < 65536) {
      return `http://localhost:${port}`;
    }
  }

  // Return default port (annotation server runs on fixed port 3001)
  return `http://localhost:${DEFAULT_ANNOTATION_SERVER_PORT}`;
}

/**
 * Get annotation server URL synchronously (same logic, but sync)
 * Use this for cases where you can't use async (like sendBeacon)
 */
export function getAnnotationServerUrlSync() {
  return getAnnotationServerUrl();
}

/**
 * Clear cached annotation server port (kept for API compatibility, but not used)
 */
export function clearAnnotationServerCache() {
  // No-op: we use fixed port or environment variable, no cache needed
}

/**
 * Manually set annotation server port (kept for API compatibility, but not used)
 */
export function setAnnotationServerPort(port) {
  // No-op: we use fixed port or environment variable, no manual setting needed
  console.warn('setAnnotationServerPort is deprecated, use VITE_ANNOTATION_SERVER_PORT environment variable instead');
}
