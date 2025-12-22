// Backend configuration utility
// Handles dynamic port detection for the backend API

const DEFAULT_BACKEND_PORT = 8000;
const MAX_PORT_ATTEMPTS = 10;

// Cache for discovered port
let cachedBackendPort = null;

/**
 * Attempts to discover the backend port by:
 * 1. Using cached port from localStorage (if available)
 * 2. Trying common ports (8000-8009) by checking /health endpoint
 * 3. Falling back to default port
 */
export async function getBackendUrl() {
  // Return cached port if available
  if (cachedBackendPort) {
    return `http://127.0.0.1:${cachedBackendPort}`;
  }

  // Try to use stored port from localStorage (persisted from previous discovery)
  try {
    const storedPort = localStorage.getItem('backend_port');
    if (storedPort) {
      const port = parseInt(storedPort, 10);
      if (port > 0 && port < 65536) {
        // Verify the port is still working
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 500);
          const response = await fetch(`http://127.0.0.1:${port}/health`, {
            method: 'GET',
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          
          if (response.ok) {
            cachedBackendPort = port;
            return `http://127.0.0.1:${port}`;
          }
        } catch (e) {
          // Port not working, continue to discovery
        }
      }
    }
  } catch (e) {
    // Ignore errors
  }

  // Try to discover port by checking common ports
  const portsToTry = [];
  for (let port = DEFAULT_BACKEND_PORT; port < DEFAULT_BACKEND_PORT + MAX_PORT_ATTEMPTS; port++) {
    portsToTry.push(port);
  }

  // Try ports in parallel (faster discovery)
  const healthChecks = portsToTry.map(async (port) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300);
      const response = await fetch(`http://127.0.0.1:${port}/health`, {
        method: 'GET',
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      
      if (response.ok) {
        return port;
      }
    } catch (e) {
      // Port not available
    }
    return null;
  });

  const results = await Promise.all(healthChecks);
  const foundPort = results.find(port => port !== null);

  if (foundPort) {
    cachedBackendPort = foundPort;
    localStorage.setItem('backend_port', foundPort.toString());
    return `http://127.0.0.1:${foundPort}`;
  }

  // Fallback to default port
  cachedBackendPort = DEFAULT_BACKEND_PORT;
  return `http://127.0.0.1:${DEFAULT_BACKEND_PORT}`;
}

/**
 * Clear cached backend port (useful when backend restarts)
 */
export function clearBackendCache() {
  cachedBackendPort = null;
  localStorage.removeItem('backend_port');
}

/**
 * Manually set backend port (for testing or manual configuration)
 */
export function setBackendPort(port) {
  cachedBackendPort = port;
  if (port) {
    localStorage.setItem('backend_port', port.toString());
  } else {
    localStorage.removeItem('backend_port');
  }
}
