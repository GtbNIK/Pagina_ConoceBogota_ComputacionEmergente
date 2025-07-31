class AITouristChatbot {
  constructor() {
    this.messageInput = document.getElementById("messageInput")
    this.sendButton = document.getElementById("sendButton")
    this.chatMessages = document.getElementById("chatMessages")
    this.loading = document.getElementById("loading")
    this.charCount = document.getElementById("charCount")

    this.initializeEventListeners()
    this.updateCharCount()
    this.showWelcomeMessage()
  }

  initializeEventListeners() {
    // Send message on Enter key
    this.messageInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        this.sendMessage()
      }
    })

    // Character count update
    this.messageInput.addEventListener("input", () => {
      this.updateCharCount()
    })

    // Send button click
    this.sendButton.addEventListener("click", () => {
      this.sendMessage()
    })
  }

  showWelcomeMessage() {
    // Mostrar mensaje de bienvenida después de un breve delay
    setTimeout(() => {
      this.addFormattedMessage(
        "💡 **Tip:** Soy tu guía especializado en Bogotá, Colombia. Puedes preguntarme:\n• '¿Qué hora es en Bogotá?'\n• '¿Qué clima hace hoy en Bogotá?'\n• '¿Dónde puedo comer ajiaco en Bogotá?'\n• '¿Cómo llego a Monserrate?'\n• '¿Qué hacer en La Candelaria?'\n• '¿Cuáles son los mejores museos de Bogotá?'",
        "bot",
      )
    }, 2000)
  }

  updateCharCount() {
    const count = this.messageInput.value.length
    this.charCount.textContent = count

    if (count > 450) {
      this.charCount.style.color = "#ef4444"
    } else if (count > 400) {
      this.charCount.style.color = "#f59e0b"
    } else {
      this.charCount.style.color = "#6b7280"
    }
  }

  async sendMessage() {
    const message = this.messageInput.value.trim()

    if (!message) return

    // Disable input while processing
    this.setInputState(false)

    // Add user message to chat
    this.addMessage(message, "user")

    // Clear input
    this.messageInput.value = ""
    this.updateCharCount()

    // Show loading
    this.showLoading(true)

    try {
      // Send message to backend
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: message }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      // Hide loading
      this.showLoading(false)

      // Add bot response with formatting
      this.addFormattedMessage(data.response, "bot")
    } catch (error) {
      console.error("Error:", error)
      this.showLoading(false)
      this.addFormattedMessage(
        "🚨 Lo siento, hubo un error conectando con la IA. Por favor, intenta de nuevo en unos momentos.",
        "bot",
      )
    } finally {
      // Re-enable input
      this.setInputState(true)
    }
  }

  addMessage(text, sender) {
    const messageDiv = document.createElement("div")
    messageDiv.className = `message ${sender}-message`

    const avatar = document.createElement("div")
    avatar.className = "message-avatar"
    avatar.innerHTML = sender === "bot" ? '<i class="fas fa-brain"></i>' : '<i class="fas fa-user"></i>'

    const content = document.createElement("div")
    content.className = "message-content"

    const paragraph = document.createElement("p")
    paragraph.textContent = text
    content.appendChild(paragraph)

    messageDiv.appendChild(avatar)
    messageDiv.appendChild(content)

    this.chatMessages.appendChild(messageDiv)
    this.scrollToBottom()
  }

  addFormattedMessage(text, sender) {
    const messageDiv = document.createElement("div")
    messageDiv.className = `message ${sender}-message`

    const avatar = document.createElement("div")
    avatar.className = "message-avatar"
    avatar.innerHTML = sender === "bot" ? '<i class="fas fa-brain"></i>' : '<i class="fas fa-user"></i>'

    const content = document.createElement("div")
    content.className = "message-content"

    // Formatear el texto con markdown básico
    const formattedText = this.formatText(text)
    content.innerHTML = formattedText

    messageDiv.appendChild(avatar)
    messageDiv.appendChild(content)

    this.chatMessages.appendChild(messageDiv)
    this.scrollToBottom()
  }

  formatText(text) {
    // Convertir markdown básico a HTML
    const formatted = text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>") // **bold**
      .replace(/\*(.*?)\*/g, "<em>$1</em>") // *italic*
      .replace(/\n\n/g, "</p><p>") // Párrafos
      .replace(/\n• /g, "<br>• ") // Lista con bullets
      .replace(/\n/g, "<br>") // Saltos de línea

    return `<p>${formatted}</p>`
  }

  async getWeatherUpdate() {
    this.showLoading(true)

    try {
      const response = await fetch("/weather")
      const data = await response.json()

      this.showLoading(false)

      if (data.formatted) {
        this.addFormattedMessage(data.formatted, "bot")
      } else {
        this.addFormattedMessage("No pude obtener la información del clima en este momento.", "bot")
      }
    } catch (error) {
      console.error("Error:", error)
      this.showLoading(false)
      this.addFormattedMessage("Error obteniendo información del clima.", "bot")
    }
  }

  async getTimeUpdate() {
    this.showLoading(true)

    try {
      const response = await fetch("/time")
      const data = await response.json()

      this.showLoading(false)

      if (data.formatted) {
        this.addFormattedMessage(data.formatted, "bot")
      } else {
        this.addFormattedMessage("No pude obtener la hora actual en este momento.", "bot")
      }
    } catch (error) {
      console.error("Error:", error)
      this.showLoading(false)
      this.addFormattedMessage("Error obteniendo la hora actual.", "bot")
    }
  }

  setInputState(enabled) {
    this.messageInput.disabled = !enabled
    this.sendButton.disabled = !enabled

    if (enabled) {
      this.messageInput.focus()
    }
  }

  showLoading(show) {
    this.loading.style.display = show ? "flex" : "none"
    if (show) {
      this.scrollToBottom()
    }
  }

  scrollToBottom() {
    setTimeout(() => {
      this.chatMessages.scrollTop = this.chatMessages.scrollHeight
    }, 100)
  }

  clearChat() {
    // Keep only the initial bot message
    const messages = this.chatMessages.querySelectorAll(".message")
    for (let i = 1; i < messages.length; i++) {
      messages[i].remove()
    }

    // Show welcome message again
    setTimeout(() => {
      this.showWelcomeMessage()
    }, 500)
  }
}

// Global functions
function sendQuickMessage(message) {
  const chatbot = window.chatbotInstance
  chatbot.messageInput.value = message
  chatbot.sendMessage()
}

function clearChat() {
  if (confirm("¿Estás seguro de que quieres limpiar el chat?")) {
    window.chatbotInstance.clearChat()
  }
}

function getWeatherUpdate() {
  window.chatbotInstance.getWeatherUpdate()
}

function getTimeUpdate() {
  window.chatbotInstance.getTimeUpdate()
}

// Initialize chatbot when page loads
document.addEventListener("DOMContentLoaded", () => {
  window.chatbotInstance = new AITouristChatbot()
})
