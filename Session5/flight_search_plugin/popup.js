// Default system prompts
const DEFAULT_SYSTEM_PROMPTS = {
  search: "You are a flight search expert. Search for flights from Germany to India considering price, duration, and layovers. Focus on finding the best value options.",
  price: "You are a price analysis expert. Analyze flight prices and identify the best deals, considering factors like seasonality, booking time, and airline reputation.",
  recommend: "You are a travel recommendation expert. Recommend the best flight options based on price, comfort, duration, and overall value for money."
};

// Current system prompts
let currentSystemPrompts = { ...DEFAULT_SYSTEM_PROMPTS };

// Load system prompts from storage
async function loadSystemPrompts() {
  try {
    const result = await chrome.storage.local.get(['systemPrompts']);
    if (result.systemPrompts) {
      currentSystemPrompts = result.systemPrompts;
    }
    updatePromptTextareas();
  } catch (error) {
    console.error('Error loading system prompts:', error);
  }
}

// Save system prompts to storage
async function saveSystemPrompts() {
  try {
    await chrome.storage.local.set({ systemPrompts: currentSystemPrompts });
  } catch (error) {
    console.error('Error saving system prompts:', error);
  }
}

// Update prompt textareas with current values
function updatePromptTextareas() {
  document.getElementById('searchPrompt').value = currentSystemPrompts.search;
  document.getElementById('pricePrompt').value = currentSystemPrompts.price;
  document.getElementById('recommendPrompt').value = currentSystemPrompts.recommend;
}

// Save a specific prompt
async function savePrompt(promptType) {
  const textarea = document.getElementById(`${promptType}Prompt`);
  const prompt = textarea.value.trim();
  
  if (!prompt) {
    alert('Please enter a valid prompt');
    return;
  }
  
  currentSystemPrompts[promptType] = prompt;
  await saveSystemPrompts();
  alert('Prompt saved successfully');
}

// Reset all prompts to defaults
async function resetPrompts() {
  if (!confirm('Are you sure you want to reset all prompts to their default values?')) {
    return;
  }
  
  currentSystemPrompts = { ...DEFAULT_SYSTEM_PROMPTS };
  await saveSystemPrompts();
  updatePromptTextareas();
  alert('Prompts reset successfully');
}

// Handle form submission
document.getElementById('searchForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  // Get form values
  const departure = document.getElementById('departure').value;
  const arrival = document.getElementById('arrival').value;
  const departureDate = document.getElementById('departureDate').value;
  const returnDate = document.getElementById('returnDate').value;
  const passengers = document.getElementById('passengers').value;
  
  // Get prompts from storage
  const prompts = await chrome.storage.local.get(['searchPrompt', 'pricePrompt', 'recommendPrompt']);
  
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
        passengers,
        prompts: {
          search: prompts.searchPrompt || 'Find flights with good value and reasonable duration',
          price: prompts.pricePrompt || 'Analyze prices and identify the best value options',
          recommend: prompts.recommendPrompt || 'Recommend flights based on price, duration, and stops'
        }
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

// Load saved prompts on popup open
document.addEventListener('DOMContentLoaded', async () => {
  const prompts = await chrome.storage.local.get(['searchPrompt', 'pricePrompt', 'recommendPrompt']);
  
  if (prompts.searchPrompt) {
    document.getElementById('searchPrompt').value = prompts.searchPrompt;
  }
  if (prompts.pricePrompt) {
    document.getElementById('pricePrompt').value = prompts.pricePrompt;
  }
  if (prompts.recommendPrompt) {
    document.getElementById('recommendPrompt').value = prompts.recommendPrompt;
  }
}); 