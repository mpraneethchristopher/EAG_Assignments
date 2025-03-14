document.addEventListener('DOMContentLoaded', () => {
  const summarizeBtn = document.getElementById('summarizeBtn');
  const summaryDiv = document.getElementById('summary');

  const FIRECRAWL_API_KEY = 'fc-5756b85bd02b445486660c07c71cabc9';
  const FIRECRAWL_API_URL = 'https://api.firecrawl.dev/v1/scrape';

  function downloadSummary(summary, url) {
    // Create timestamp in format: YYYY-MM-DD_HH-MM-SS
    const now = new Date();
    const timestamp = now.toISOString()
      .replace(/[:.]/g, '-')
      .replace('T', '_')
      .replace('Z', '');

    // Get the page title or domain name for the filename
    const domain = new URL(url).hostname.replace('www.', '');
    const filename = `summary_${domain}_${timestamp}.txt`;

    // Create the content with metadata
    const content = `Summary of: ${url}\nDate: ${now.toLocaleString()}\n\n${summary}`;

    // Create blob and download link
    const blob = new Blob([content], { type: 'text/plain' });
    const downloadUrl = URL.createObjectURL(blob);
    const downloadLink = document.createElement('a');
    downloadLink.href = downloadUrl;
    downloadLink.download = filename;

    // Trigger download
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    URL.revokeObjectURL(downloadUrl);
  }

  async function generateSummary(url) {
    if (!url || !url.startsWith('http')) {
      throw new Error('Invalid URL');
    }

    try {
      console.log('Making API request to:', FIRECRAWL_API_URL);
      console.log('Requesting summary for URL:', url);
      
      const response = await fetch(FIRECRAWL_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${FIRECRAWL_API_KEY}`,
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          url: url,
          formats: ['json'],
          jsonOptions: {
            schema: {
              type: "object",
              properties: {
                summary: {
                  type: "string",
                  description: "A concise summary of the article's main points"
                }
              },
              required: ["summary"]
            }
          }
        })
      });

      console.log('API Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.text();
        console.error('API Error:', errorData);
        
        if (response.status === 401) {
          throw new Error('Invalid API key. Please check your API key and try again.');
        } else if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please try again later.');
        } else {
          throw new Error(`API Error: ${response.status} - ${errorData}`);
        }
      }

      const data = await response.json();
      if (!data || !data.data || !data.data.json || !data.data.json.summary) {
        throw new Error('Invalid response from API');
      }

      return data.data.json.summary;
    } catch (error) {
      console.error('Error in generateSummary:', error);
      if (error.message.includes('Failed to fetch')) {
        throw new Error('Unable to connect to the API. Please check your internet connection and try again.');
      }
      throw error;
    }
  }

  summarizeBtn.addEventListener('click', async () => {
    try {
      // Disable button and show loading state
      summarizeBtn.disabled = true;
      summaryDiv.innerHTML = '<div class="loading">Generating summary...</div>';

      // Get the current active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab) {
        throw new Error('No active tab found');
      }

      if (!tab.url || !tab.url.startsWith('http')) {
        throw new Error('Cannot summarize this page. Please try with a regular web page.');
      }

      // Generate summary using Firecrawl API with the current page URL
      const summary = await generateSummary(tab.url);

      // Display the summary and add download button
      summaryDiv.innerHTML = `
        <h3>Summary:</h3>
        <p>${summary}</p>
        <button id="downloadBtn" class="download-btn">Download Summary</button>
      `;

      // Add click handler for download button
      document.getElementById('downloadBtn').addEventListener('click', () => {
        downloadSummary(summary, tab.url);
      });
    } catch (error) {
      console.error('Error in click handler:', error);
      summaryDiv.innerHTML = `
        <div class="error">
          ${error.message || 'Failed to generate summary'}
        </div>
      `;
    } finally {
      summarizeBtn.disabled = false;
    }
  });
}); 