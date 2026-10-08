// API client for AgriGuard Backend

const API_BASE = "/api";

function getHeaders(isMultipart = false) {
  const token = localStorage.getItem("agriguard_token");
  const headers = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (!isMultipart) {
    headers["Content-Type"] = "application/json";
  }
  return headers;
}

export const api = {
  // Auth
  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }
    const data = await res.json();
    localStorage.setItem("agriguard_token", data.access_token);
    localStorage.setItem("agriguard_user", JSON.stringify(data.user));
    return data;
  },

  async register(name, email, password, role = "farmer", preferred_language = "en") {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, role, preferred_language })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed");
    }
    const data = await res.json();
    localStorage.setItem("agriguard_token", data.access_token);
    localStorage.setItem("agriguard_user", JSON.stringify(data.user));
    return data;
  },

  async getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getHeaders()
    });
    if (!res.ok) {
      throw new Error("Unauthorized");
    }
    return res.json();
  },

  logout() {
    localStorage.removeItem("agriguard_token");
    localStorage.removeItem("agriguard_user");
  },

  // Supported crops
  async getSupportedCrops() {
    const res = await fetch(`${API_BASE}/supported-crops`);
    if (!res.ok) throw new Error("Failed to fetch supported crops");
    return res.json();
  },

  // Reports
  async uploadReport(formData) {
    const res = await fetch(`${API_BASE}/reports`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Analysis failed");
    }
    return res.json();
  },

  async getReports(params = {}) {
    const query = new URLSearchParams();
    if (params.crop) query.append("crop", params.crop);
    if (params.severity) query.append("severity", params.severity);
    if (params.status) query.append("status", params.status);
    if (params.search) query.append("search", params.search);

    const res = await fetch(`${API_BASE}/reports?${query.toString()}`, {
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to fetch reports");
    return res.json();
  },

  async getReport(id) {
    const res = await fetch(`${API_BASE}/reports/${id}`, {
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Report not found");
    return res.json();
  },

  async deleteReport(id) {
    const res = await fetch(`${API_BASE}/reports/${id}`, {
      method: "DELETE",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to delete report");
    return true;
  },

  // Chat
  async sendChatMessage(message, report_id = null, conversation_id = null) {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ message, report_id, conversation_id })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to send chat message");
    }
    return res.json();
  },

  async getConversations() {
    const res = await fetch(`${API_BASE}/conversations`, {
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to fetch conversations");
    return res.json();
  },

  async getMessages(conversationId) {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to fetch messages");
    return res.json();
  },

  async deleteConversation(conversationId) {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}`, {
      method: "DELETE",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to delete conversation");
    return true;
  },

  // Expert
  async getExpertReports() {
    const res = await fetch(`${API_BASE}/expert/reports`, {
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to fetch expert queue");
    return res.json();
  },

  async submitExpertReview(reportId, verdict, comment) {
    const res = await fetch(`${API_BASE}/reports/${reportId}/review`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ verdict, comment })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to submit review");
    }
    return res.json();
  },

  // Metrics
  async getMetricsSummary() {
    const res = await fetch(`${API_BASE}/metrics/summary`);
    if (!res.ok) throw new Error("Failed to fetch metrics");
    return res.json();
  }
};
