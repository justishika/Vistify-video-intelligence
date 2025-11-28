import { state } from "./model.js";

const metaDataParent = document.querySelector(".meta-data-container");
const summaryParent = document.querySelector(".summary-container");
const button1 = document.querySelector("#button1");
const button2 = document.querySelector("#button2");
const search = document.querySelector("#search-input");

export const displayMetaData = function () {
    clear(metaDataParent);
    const markup = `
        <div id="video-title">${state.title}</div>
        <div id="video-thumbnail"><img src="${state.thumbnailUrl}"></div>
    `;
    metaDataParent.insertAdjacentHTML("afterbegin", markup);
};

export const getVideoUrl = function () {
    return search.value;
};

const clear = function (element) {
    element.innerHTML = "";
};

export const renderSpinnerMetaData = function () {
    clear(metaDataParent);
    const markup = `<div class="spinner"></div>`;
    metaDataParent.insertAdjacentHTML("afterbegin", markup);
};

export const renderSpinnerSummary = function () {
    clear(summaryParent);
    const markup = `
        <div class="summary">
            <h2>Video Summary:</h2>
            <div class="spinner-container">
                <div class="spinner"></div>
            </div>
        </div>`;
    summaryParent.insertAdjacentHTML("afterbegin", markup);
};

export const renderSummary = function () {
    clear(summaryParent);
    const summary = state.summary
        .replace(/\n/g, "<br>")
        .replace(/(\d+)\./g, "<b>$1.</b>");
    
    const markup = `
        <div class="summary">
            <h2>Video Summary:</h2>
            <div class="summary-text">${summary}</div>
            
            <!-- Q&A Section -->
            <div class="qa-section">
                <button class="btn-qa-toggle" id="qa-toggle">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                    Ask Questions About This Video
                </button>
                
                <div class="qa-container" id="qa-container" style="display: none;">
                    <div class="insights-section" id="insights-section">
                        <button class="btn-insights" id="btn-insights">
                            💡 Get Video Insights & Suggested Questions
                        </button>
                        <div id="insights-content"></div>
                    </div>
                    
                    <div class="conversation" id="conversation"></div>
                    
                    <div class="qa-input-section">
                        <div class="qa-input-wrapper">
                            <input 
                                type="text" 
                                id="qa-input" 
                                placeholder="Ask anything about the video..."
                                autocomplete="off"
                            />
                            <button class="btn-send" id="btn-send">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"></path>
                                </svg>
                            </button>
                        </div>
                        <button class="btn-clear-chat" id="btn-clear">Clear Conversation</button>
                    </div>
                </div>
            </div>
        </div>`;
    
    summaryParent.insertAdjacentHTML("afterbegin", markup);
};

export const renderQAToggle = function (handler) {
    const toggleBtn = document.querySelector("#qa-toggle");
    const qaContainer = document.querySelector("#qa-container");
    
    if (toggleBtn && qaContainer) {
        toggleBtn.addEventListener("click", function () {
            const isVisible = qaContainer.style.display !== "none";
            qaContainer.style.display = isVisible ? "none" : "block";
            toggleBtn.textContent = isVisible ? "Ask Questions About This Video" : "Hide Q&A";
            
            // Add icon back
            if (isVisible) {
                toggleBtn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                    Ask Questions About This Video`;
            } else {
                toggleBtn.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M18 6L6 18M6 6l12 12"></path>
                    </svg>
                    Hide Q&A`;
            }
        });
    }
};

export const addQAHandlers = function (askHandler, clearHandler, insightsHandler) {
    renderQAToggle();
    
    const sendBtn = document.querySelector("#btn-send");
    const qaInput = document.querySelector("#qa-input");
    const clearBtn = document.querySelector("#btn-clear");
    const insightsBtn = document.querySelector("#btn-insights");
    
    if (sendBtn && qaInput) {
        const handleSend = function () {
            const question = qaInput.value.trim();
            if (question) {
                askHandler(question);
                qaInput.value = "";
            }
        };
        
        sendBtn.addEventListener("click", handleSend);
        qaInput.addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                handleSend();
            }
        });
    }
    
    if (clearBtn) {
        clearBtn.addEventListener("click", clearHandler);
    }
    
    if (insightsBtn) {
        insightsBtn.addEventListener("click", insightsHandler);
    }
};

export const renderQuestion = function (question) {
    const conversation = document.querySelector("#conversation");
    if (!conversation) return;
    
    const markup = `
        <div class="message user-message">
            <div class="message-content">${escapeHtml(question)}</div>
        </div>
        <div class="message ai-message">
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;
    
    conversation.insertAdjacentHTML("beforeend", markup);
    conversation.scrollTop = conversation.scrollHeight;
};

export const renderAnswer = function (answer) {
    const conversation = document.querySelector("#conversation");
    if (!conversation) return;
    
    const messages = conversation.querySelectorAll(".ai-message");
    const lastMessage = messages[messages.length - 1];
    
    if (lastMessage) {
        const formattedAnswer = answer
            .replace(/\n/g, "<br>")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>");
        
        lastMessage.querySelector(".message-content").innerHTML = formattedAnswer;
        conversation.scrollTop = conversation.scrollHeight;
    }
};

export const clearConversation = function () {
    const conversation = document.querySelector("#conversation");
    if (conversation) {
        conversation.innerHTML = "";
    }
};

export const renderInsights = function (insights) {
    const insightsContent = document.querySelector("#insights-content");
    if (!insightsContent) return;
    
    const formattedInsights = insights
        .replace(/\n/g, "<br>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>");
    
    insightsContent.innerHTML = `
        <div class="insights-box">
            ${formattedInsights}
        </div>
    `;
};

export const showInsightsLoading = function () {
    const insightsContent = document.querySelector("#insights-content");
    if (insightsContent) {
        insightsContent.innerHTML = `
            <div class="spinner-container">
                <div class="spinner"></div>
            </div>
        `;
    }
};

export const renderError = function (errorMessage) {
    clear(metaDataParent);
    clear(summaryParent);
    const markup = `
        <div class="error">
            <div class="error-text">${errorMessage}</div>
        </div>`;
    metaDataParent.insertAdjacentHTML("afterbegin", markup);
};

export const renderQAError = function (errorMessage) {
    const conversation = document.querySelector("#conversation");
    if (!conversation) return;
    
    const messages = conversation.querySelectorAll(".ai-message");
    const lastMessage = messages[messages.length - 1];
    
    if (lastMessage) {
        lastMessage.querySelector(".message-content").innerHTML = `
            <span style="color: #fca5a5;">❌ ${escapeHtml(errorMessage)}</span>
        `;
    }
};

export const scrollToSummary = function () {
    summaryParent.scrollIntoView({ behavior: "smooth", block: "start" });
};

export const addHandlerSearch = function (handler) {
    button1.addEventListener("click", function (e) {
        e.preventDefault();
        handler('short');
    });
    
    button2.addEventListener("click", function (e) {
        e.preventDefault();
        handler('detailed');
    });
};

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}