const API_BASE = "";

export const getApiUrl = (path) => `${API_BASE}${path}`;

/**
 * Sends a query to the legal chatbot and handles the streaming response.
 * @param {string} query - The user query
 * @param {string} language - "English" or "Tamil"
 * @param {Array} history - Array of { role, text } message history
 * @param {function} onChunk - Callback triggered when a text chunk is received
 * @param {function} onDone - Callback triggered when the stream finishes
 * @param {function} onError - Callback triggered on failure
 */
export const chatWithNeedhi = async (query, language, history, onChunk, onDone, onError) => {
  try {
    const response = await fetch(getApiUrl("/api/chat"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query, language, history }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    let fullText = "";

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        const chunk = decoder.decode(value, { stream: !done });
        fullText += chunk;
        onChunk(chunk, fullText);
      }
    }
    onDone(fullText);
  } catch (error) {
    console.error("Chat error:", error);
    onError(error);
  }
};

/**
 * Uploads a document (PDF/Image) for AI summarization.
 */
export const analyzeDocument = async (file, question) => {
  const formData = new FormData();
  formData.append("file", file);
  if (question) {
    formData.append("question", question);
  }

  const response = await fetch(getApiUrl("/api/analyze-doc"), {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Error analyzing document");
  }

  return response.json();
};

/**
 * Searches the IPC vs BNS database.
 */
export const bnsLookup = async (term = "", category = "") => {
  const response = await fetch(getApiUrl("/api/bns-lookup"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ term, category }),
  });

  if (!response.ok) {
    throw new Error("Failed to search BNS mappings");
  }

  return response.json();
};

/**
 * Performs BNS vs IPC comparison using AI.
 */
export const compareBnsAi = async (query) => {
  const response = await fetch(getApiUrl("/api/bns-compare-ai"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error("Failed BNS AI comparison");
  }

  return response.json();
};

/**
 * Subscribes to email alerts for a case.
 */
export const subscribeToCase = async (cnr, email, clientName, language = "English") => {
  const response = await fetch(getApiUrl("/api/cases/subscribe"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ cnr, email, client_name: clientName, language }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to subscribe to case updates");
  }

  return response.json();
};

/**
 * Searches case registry.
 */
export const searchCases = async (search = "", searchType = "CNR Number") => {
  const url = getApiUrl(`/api/cases?search=${encodeURIComponent(search)}&search_type=${encodeURIComponent(searchType)}`);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Failed to fetch cases");
  }
  return response.json();
};

/**
 * Searches mock lawyer directory.
 */
export const searchLawyers = async (specialization = "", city = "", search = "") => {
  const url = getApiUrl(`/api/lawyers?specialization=${encodeURIComponent(specialization)}&city=${encodeURIComponent(city)}&search=${encodeURIComponent(search)}`);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error("Failed to fetch lawyers");
  }
  return response.json();
};

/**
 * Generates an FIR draft.
 */
export const generateFir = async (issue, state, ps, name, category = null, categoryFields = null) => {
  const response = await fetch(getApiUrl("/api/generate-fir"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ issue, state, ps, name, category, category_fields: categoryFields }),
  });

  if (!response.ok) {
    throw new Error("Failed to generate FIR");
  }

  return response.json();
};

/**
 * Generates a legal template document.
 */
export const generateTemplate = async (templateType, fields) => {
  const response = await fetch(getApiUrl("/api/generate-template"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ template_type: templateType, fields }),
  });

  if (!response.ok) {
    throw new Error("Failed to generate template");
  }

  return response.json();
};

/**
 * Submits text content to be compiled into a custom PDF and downloads it.
 */
export const downloadPdf = async (title, text, defaultFilename = "Document.pdf") => {
  try {
    const response = await fetch(getApiUrl("/api/generate-pdf"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title, text }),
    });

    if (!response.ok) {
      throw new Error("Failed to generate PDF");
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = defaultFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error("PDF generation failed:", error);
    alert("Error downloading PDF: " + error.message);
  }
};

/**
 * Books an appointment with a lawyer.
 */
export const bookLawyer = async (bookingData) => {
  const response = await fetch(getApiUrl("/api/book-lawyer"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(bookingData),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to confirm lawyer booking");
  }

  return response.json();
};

/**
 * Sends a query to chat about an uploaded document and handles the streaming response.
 */
export const chatWithDocument = async (docText, query, language, history, onChunk, onDone, onError) => {
  try {
    const response = await fetch(getApiUrl("/api/chat-doc"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ doc_text: docText, query, language, history }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let done = false;
    let fullText = "";

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        const chunk = decoder.decode(value, { stream: !done });
        fullText += chunk;
        onChunk(chunk, fullText);
      }
    }
    onDone(fullText);
  } catch (error) {
    console.error("Document Chat error:", error);
    onError(error);
  }
};

/**
 * Queries Gemini for a case outcome prediction.
 */
export const predictCaseOutcome = async (offense, narrative, evidence, priorRecord, jurisdiction, language) => {
  const response = await fetch(getApiUrl("/api/predict-outcome"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      offense,
      narrative,
      evidence,
      prior_record: priorRecord,
      jurisdiction,
      language
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to predict case outcome");
  }

  return response.json();
};

/**
 * Simplifies a pasted legal text snippet.
 */
export const simplifyLegalText = async (text, targetLanguage) => {
  const response = await fetch(getApiUrl("/api/simplify-text"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text, target_language: targetLanguage }),
  });

  if (!response.ok) {
    throw new Error("Failed to simplify legal text");
  }

  return response.json();
};
