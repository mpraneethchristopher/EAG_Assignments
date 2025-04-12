// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'searchFlights') {
    handleFlightSearch(request.params)
      .then(results => sendResponse({ results }))
      .catch(error => sendResponse({ error: error.message }));
    return true; // Required for async response
  }
});

// Handle flight search
async function handleFlightSearch(params) {
  const { departure, arrival, departureDate, returnDate, passengers } = params;
  
  try {
    // Send request to Python server
    const response = await fetch('http://localhost:5000/api/search-flights', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        departure,
        arrival,
        departureDate,
        returnDate,
        passengers
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.results;
  } catch (error) {
    console.error('Error in flight search:', error);
    throw new Error('Failed to search for flights');
  }
}

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('Smart Flight Finder extension installed');
}); 