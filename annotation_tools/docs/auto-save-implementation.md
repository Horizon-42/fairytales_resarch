# Auto-Save Implementation Guide

## Overview

This document explains the auto-save functionality implemented in the Fairy Tale Annotation Tool. The system includes two types of auto-save:

1. **Periodic Auto-Save**: Saves data every 5 minutes while editing
2. **Before Unload Auto-Save**: Saves data when the user refreshes or closes the page

## Table of Contents

1. [Why Auto-Save?](#why-auto-save)
2. [Implementation Details](#implementation-details)
3. [The `beforeunload` Event](#the-beforeunload-event)
4. [Data Sending Strategies](#data-sending-strategies)
5. [Code Walkthrough](#code-walkthrough)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Why Auto-Save?

Auto-save prevents data loss in several scenarios:

- **Accidental page refresh** (F5, Cmd/Ctrl+R)
- **Browser tab/window closure**
- **Navigation away from the page**
- **Browser crashes or system shutdowns**
- **Network interruptions during manual saves**

Without auto-save, users risk losing hours of annotation work.

---

## Implementation Details

### Periodic Auto-Save

**Location**: `App.jsx` (lines ~242-252)

```javascript
useEffect(() => {
  const interval = setInterval(() => {
    if (selectedStoryIndex !== -1) {
      console.log("Triggering auto-save...");
      saveRef.current("v1", true);
      saveRef.current("v2", true);
    }
  }, 5 * 60 * 1000); // Every 5 minutes

  return () => clearInterval(interval);
}, [selectedStoryIndex]);
```

**How it works**:
- Uses `setInterval` to trigger saves every 5 minutes
- Only saves if a story is selected (`selectedStoryIndex !== -1`)
- Saves both V1 and V2 formats silently (no alerts)
- Cleans up the interval when the component unmounts

### Before Unload Auto-Save

**Location**: `App.jsx` (lines ~254-303)

This is the more critical auto-save mechanism, triggered when the user is about to leave the page.

---

## The `beforeunload` Event

### What is `beforeunload`?

The `beforeunload` event fires when the browser is about to unload the page. This happens when:

- User refreshes the page (F5, Cmd/Ctrl+R)
- User closes the tab or browser window
- User navigates to a different URL
- User clicks the browser's back/forward button (in some cases)

### Event Limitations

⚠️ **Important**: Modern browsers have strict limitations on `beforeunload`:

1. **No async operations**: You cannot use `async/await` or promises
2. **Limited time**: The browser may terminate the page before operations complete
3. **User confirmation**: You can show a confirmation dialog, but it's often ignored by users
4. **No guarantee**: The event may not fire in all scenarios (e.g., force quit)

### Basic Usage

```javascript
window.addEventListener("beforeunload", (e) => {
  // Save data here
  // Note: This must be synchronous or use special APIs
});
```

---

## Data Sending Strategies

Because `beforeunload` has limitations, we use two strategies in order of preference:

### Strategy 1: `navigator.sendBeacon` (Preferred)

**What is it?**
- A modern browser API designed specifically for sending data during page unload
- Non-blocking: doesn't delay page navigation
- Guaranteed delivery: browser queues the request even after page closes

**How it works**:
```javascript
if (navigator.sendBeacon) {
  const blob = new Blob([payload], { type: 'application/json' });
  const sent = navigator.sendBeacon("http://localhost:3001/api/save", blob);
  if (sent) {
    console.log("Data sent successfully");
    return;
  }
}
```

**Advantages**:
- ✅ Non-blocking (doesn't freeze the UI)
- ✅ Reliable delivery even after page closes
- ✅ Designed for this exact use case
- ✅ Works in modern browsers

**Disadvantages**:
- ❌ Only sends data (no response handling)
- ❌ Limited to POST requests
- ❌ May not work in very old browsers

**Data Format**:
- Can send: `Blob`, `FormData`, `ArrayBuffer`, `URLSearchParams`, or `string`
- We use `Blob` with `application/json` type

### Strategy 2: Synchronous XMLHttpRequest (Fallback)

**What is it?**
- Traditional XHR with `async: false`
- Blocks the page until the request completes
- Not recommended for normal use, but acceptable in `beforeunload`

**How it works**:
```javascript
const xhr = new XMLHttpRequest();
xhr.open("POST", "http://localhost:3001/api/save", false); // false = synchronous
xhr.setRequestHeader("Content-Type", "application/json");
xhr.send(payload);

if (xhr.status === 200) {
  console.log("Saved successfully");
}
```

**Advantages**:
- ✅ Works in all browsers
- ✅ Can check response status
- ✅ Guaranteed to complete before page unloads (if browser allows)

**Disadvantages**:
- ❌ Blocks the page (bad UX in normal scenarios)
- ❌ May be cancelled by browser if it takes too long
- ❌ Deprecated in modern web standards (but still works)

**When to use**:
- As a fallback when `sendBeacon` is not available
- When you need to verify the save succeeded

---

## Code Walkthrough

### Complete Implementation

```javascript
// Save before page unload/refresh
useEffect(() => {
  const handleBeforeUnload = (e) => {
    // 1. Check if there's data to save
    if (selectedStoryIndex === -1) return;
    
    const currentStory = storyFiles[selectedStoryIndex];
    if (!currentStory) return;

    // 2. Helper function to save one version
    const saveData = (version) => {
      const data = version === "v2" ? jsonV2 : jsonV1;
      const payload = JSON.stringify({
        originalPath: currentStory.path,
        content: data,
        version: version
      });

      // 3. Try sendBeacon first (preferred method)
      if (navigator.sendBeacon) {
        const blob = new Blob([payload], { type: 'application/json' });
        const sent = navigator.sendBeacon("http://localhost:3001/api/save", blob);
        if (sent) {
          console.log(`Auto-saved ${version} via sendBeacon before page unload`);
          return; // Success, exit early
        }
      }

      // 4. Fallback to synchronous XHR
      try {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "http://localhost:3001/api/save", false);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send(payload);
        
        if (xhr.status === 200) {
          console.log(`Auto-saved ${version} before page unload`);
        } else {
          console.warn(`Auto-save ${version} failed: ${xhr.status}`);
        }
      } catch (err) {
        console.error(`Auto-save ${version} error:`, err);
      }
    };

    // 5. Save both V1 and V2 formats
    saveData("v1");
    saveData("v2");
  };

  // 6. Register the event listener
  window.addEventListener("beforeunload", handleBeforeUnload);

  // 7. Cleanup on unmount
  return () => {
    window.removeEventListener("beforeunload", handleBeforeUnload);
  };
}, [selectedStoryIndex, storyFiles, jsonV1, jsonV2]);
```

### Step-by-Step Explanation

1. **Conditional Check**: Only save if a story is selected
2. **Data Preparation**: Convert data to JSON string
3. **Primary Method**: Try `sendBeacon` first (non-blocking)
4. **Fallback Method**: Use synchronous XHR if `sendBeacon` fails
5. **Save Both Formats**: Save V1 and V2 to ensure compatibility
6. **Event Registration**: Add listener when component mounts
7. **Cleanup**: Remove listener when component unmounts

### Dependencies

The `useEffect` depends on:
- `selectedStoryIndex`: Which story is currently selected
- `storyFiles`: List of available stories
- `jsonV1`, `jsonV2`: The data to save

These dependencies ensure the save function always has the latest data.

---

## Best Practices

### 1. Always Use Both Methods

```javascript
// Good: Try sendBeacon, fallback to XHR
if (navigator.sendBeacon) {
  // Try sendBeacon
} else {
  // Fallback to XHR
}
```

### 2. Keep Payloads Small

Large payloads may:
- Fail to send before page unloads
- Be rejected by `sendBeacon` (size limits)
- Cause browser to cancel the request

**Solution**: Only save essential data, or compress it.

### 3. Don't Rely on User Confirmation

```javascript
// Bad: User might click "Leave" anyway
e.preventDefault();
e.returnValue = ''; // Shows confirmation dialog

// Good: Save silently, don't block user
// Just save the data without confirmation
```

### 4. Handle Errors Gracefully

```javascript
try {
  // Save attempt
} catch (err) {
  console.error("Save failed:", err);
  // Don't throw - page is unloading anyway
}
```

### 5. Test in Different Browsers

Different browsers handle `beforeunload` differently:
- Chrome: Generally reliable
- Firefox: May cancel requests if too slow
- Safari: Stricter time limits
- Edge: Similar to Chrome

### 6. Consider LocalStorage as Backup

For critical data, also save to `localStorage`:

```javascript
// Save to localStorage as backup
try {
  localStorage.setItem('auto-save-backup', JSON.stringify(data));
} catch (err) {
  // localStorage might be full or disabled
}
```

---

## Troubleshooting

### Problem: Auto-save doesn't work

**Possible causes**:
1. **Browser blocks the request**: Some browsers cancel requests that take too long
2. **Network issues**: Server might be unreachable
3. **CORS errors**: Check server CORS settings
4. **Event not firing**: Browser might be preventing `beforeunload`

**Solutions**:
- Check browser console for errors
- Verify server is running and accessible
- Test with different browsers
- Use browser DevTools Network tab to see if requests are sent

### Problem: Data saved but incomplete

**Possible causes**:
1. **Page unloads too fast**: Request cancelled before completion
2. **Large payload**: Data too big to send in time
3. **Server timeout**: Server takes too long to respond

**Solutions**:
- Reduce payload size
- Optimize server response time
- Use `sendBeacon` (more reliable for large data)

### Problem: Multiple saves triggered

**Possible causes**:
1. **Event listener added multiple times**: Not cleaning up properly
2. **Component re-renders**: `useEffect` runs multiple times

**Solutions**:
- Always return cleanup function from `useEffect`
- Check dependencies array to prevent unnecessary re-runs

### Debugging Tips

1. **Add console logs**:
```javascript
console.log("Before unload triggered");
console.log("Sending data:", payload);
console.log("SendBeacon result:", sent);
```

2. **Check Network tab**: See if requests appear in browser DevTools

3. **Test with small delays**:
```javascript
// Add small delay to see if request completes
setTimeout(() => {
  // Save logic
}, 100);
```

4. **Monitor server logs**: Check if requests reach the server

---

## Additional Resources

- [MDN: beforeunload event](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event)
- [MDN: navigator.sendBeacon](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/sendBeacon)
- [MDN: XMLHttpRequest](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest)
- [Web.dev: Page Lifecycle API](https://web.dev/page-lifecycle-api/)

---

## Summary

Auto-save is crucial for preventing data loss. The implementation uses:

1. **Periodic saves**: Every 5 minutes during editing
2. **Before unload saves**: When user leaves the page
3. **Dual strategy**: `sendBeacon` (preferred) + synchronous XHR (fallback)
4. **Error handling**: Graceful degradation if saves fail

Remember: Auto-save is a safety net, not a replacement for manual saves. Always encourage users to save manually when possible.

