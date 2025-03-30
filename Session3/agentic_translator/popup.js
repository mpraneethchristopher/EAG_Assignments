// Function to display logs
function displayLogs() {
  const logContainer = document.getElementById('logContainer');
  
  // Retrieve logs from storage
  chrome.storage.local.get(['translationLogs'], (result) => {
    const logs = result.translationLogs || [];
    
    if (logs.length === 0) {
      logContainer.innerHTML = '<div class="log-entry">No logs yet. Translate some text to see the agent in action.</div>';
      return;
    }
    
    logContainer.innerHTML = '';
    
    // Display logs in order (as they come from the Python API)
    logs.forEach((log) => {
      const logEntry = document.createElement('div');
      logEntry.className = 'log-entry';
      
      if (log.type === 'function_call') {
        logEntry.innerHTML = `<span class="function-call">FUNCTION_CALL:</span> ${log.function}|${log.params}<br>`;
        if (log.result) {
          logEntry.innerHTML += `<span class="result">Result:</span> ${log.result}`;
        }
      } else if (log.type === 'final_answer') {
        logEntry.innerHTML = `<span class="function-call">FINAL_ANSWER:</span> "${log.translation}"`;
      } else if (log.type === 'error') {
        logEntry.innerHTML = `<span class="error">ERROR:</span> ${log.message}`;
      } else {
        logEntry.textContent = log.message || JSON.stringify(log);
      }
      
      // Add timestamp if available
      if (log.timestamp) {
        const timestamp = document.createElement('div');
        timestamp.style.fontSize = '10px';
        timestamp.style.color = '#999';
        timestamp.style.marginTop = '4px';
        timestamp.textContent = new Date(log.timestamp).toLocaleString();
        logEntry.appendChild(timestamp);
      }
      
      logContainer.appendChild(logEntry);
    });
  });
}

// Clear logs button handler
document.getElementById('clearLogs').addEventListener('click', () => {
  // Call the Python API to clear logs
  fetch('http://localhost:5000/api/clear_logs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => response.json())
  .then(() => {
    // Also clear logs in local storage
    chrome.storage.local.set({ 'translationLogs': [] }, () => {
      displayLogs();
    });
  })
  .catch(error => {
    console.error('Error clearing logs:', error);
    // Still clear local storage
    chrome.storage.local.set({ 'translationLogs': [] }, () => {
      displayLogs();
    });
  });
});

// Display logs when popup opens
document.addEventListener('DOMContentLoaded', displayLogs);

// Listen for log updates
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local' && changes.translationLogs) {
    displayLogs();
  }
}); 