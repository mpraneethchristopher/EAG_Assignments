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

// System Prompts Management
async function loadSystemPrompts() {
  try {
    const response = await fetch('http://localhost:5000/api/system-prompts');
    const prompts = await response.json();
    
    // Update textareas with current prompts
    document.getElementById('detectLanguagePrompt').value = prompts.detect_language;
    document.getElementById('translatePrompt').value = prompts.translate;
    document.getElementById('postprocessPrompt').value = prompts.postprocess;
  } catch (error) {
    console.error('Error loading system prompts:', error);
  }
}

async function savePrompt(promptType) {
  const textarea = document.getElementById(`${promptType}Prompt`);
  const prompt = textarea.value.trim();
  
  if (!prompt) {
    alert('Please enter a valid prompt');
    return;
  }
  
  try {
    const response = await fetch('http://localhost:5000/api/system-prompts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: promptType,
        prompt: prompt
      })
    });
    
    if (response.ok) {
      alert('Prompt saved successfully');
    } else {
      const error = await response.json();
      alert(`Error saving prompt: ${error.error}`);
    }
  } catch (error) {
    console.error('Error saving prompt:', error);
    alert('Error saving prompt. Please try again.');
  }
}

async function resetPrompts() {
  if (!confirm('Are you sure you want to reset all prompts to their default values?')) {
    return;
  }
  
  try {
    const response = await fetch('http://localhost:5000/api/system-prompts/reset', {
      method: 'POST'
    });
    
    if (response.ok) {
      await loadSystemPrompts();
      alert('Prompts reset successfully');
    } else {
      const error = await response.json();
      alert(`Error resetting prompts: ${error.error}`);
    }
  } catch (error) {
    console.error('Error resetting prompts:', error);
    alert('Error resetting prompts. Please try again.');
  }
}

// Load system prompts when popup opens
document.addEventListener('DOMContentLoaded', () => {
  loadSystemPrompts();
  // ... existing event listeners ...
}); 