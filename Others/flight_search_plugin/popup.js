// Handle form submission
document.getElementById('searchForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  // Get form values
  const departure = document.getElementById('departure').value;
  const arrival = document.getElementById('arrival').value;
  const departureDate = document.getElementById('departureDate').value;
  const returnDate = document.getElementById('returnDate').value;
  const passengers = document.getElementById('passengers').value;
  
  // Show loading state
  document.getElementById('results').innerHTML = '<div class="loading">Searching for flights...</div>';
  
  try {
    // Send message to background script
    const response = await chrome.runtime.sendMessage({
      action: 'searchFlights',
      params: {
        departure,
        arrival,
        departureDate,
        returnDate,
        passengers
      }
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    // Display results
    displayResults(response.results);
  } catch (error) {
    document.getElementById('results').innerHTML = `<div class="error">Error: ${error.message}</div>`;
  }
});

// Display flight results
function displayResults(flights) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';
  
  if (flights.length === 0) {
    resultsDiv.innerHTML = '<div class="no-results">No flights found matching your criteria</div>';
    return;
  }
  
  const flightsList = document.createElement('div');
  flightsList.className = 'flights-list';
  
  flights.forEach(flight => {
    const flightCard = document.createElement('div');
    flightCard.className = 'flight-card';
    
    flightCard.innerHTML = `
      <div class="flight-header">
        <span class="airline">${flight.airline}</span>
        <span class="price">${flight.price}</span>
      </div>
      <div class="flight-details">
        <div class="time">
          <span class="departure">${flight.departureTime}</span>
          <span class="duration">${flight.duration}</span>
          <span class="arrival">${flight.arrivalTime}</span>
        </div>
        <div class="stops">${flight.stops}</div>
        <div class="source">Source: ${flight.source}</div>
        ${flight.recommendation ? `<div class="recommendation">${flight.recommendation}</div>` : ''}
      </div>
    `;
    
    flightsList.appendChild(flightCard);
  });
  
  resultsDiv.appendChild(flightsList);
}

// Initialize the popup
document.addEventListener('DOMContentLoaded', () => {
  // Set minimum date for date inputs to today
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('departureDate').min = today;
  document.getElementById('returnDate').min = today;
}); 