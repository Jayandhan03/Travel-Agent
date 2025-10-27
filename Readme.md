✈️ AI Trip Planner
Your personal AI travel agent that crafts detailed, personalized trip itineraries. Powered by a multi-agent system orchestrated with LangGraph, leveraging Google's Gemini for reasoning and SerpApi for real-time data.
![alt text](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![alt text](https://img.shields.io/badge/Streamlit-1.33+-orange?style=for-the-badge&logo=streamlit)
![alt text](https://img.shields.io/badge/LangChain-0.1+-green?style=for-the-badge&logo=langchain)
![alt text](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)
![alt text](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)
<!-- Replace with your actual app URL! -->
🌟 Demo
This application provides a seamless experience for travel planning. Simply input your destination, dates, and preferences, and let the AI agents collaborate to build your perfect trip from scratch.
[ HIGHLY RECOMMENDED: INSERT A GIF DEMO HERE ]
A short GIF showcasing the app's functionality—from filling out the form to the final, beautifully rendered itinerary—would be the most impactful element of this README. You can use tools like LiceCAP or Giphy Capture to record your screen.
![alt text](https://user-images.githubusercontent.com/12345/67890.png)
<!-- Replace this with a real screenshot or GIF -->
✨ Features
📝 Dynamic Itinerary Generation: Get a full day-by-day plan, including activities and meal suggestions.
🌐 Real-time Data Integration: Fetches up-to-date information for:
Visa Requirements: Checks entry requirements for your destination.
Weather Forecasts: Provides a detailed weather outlook for your travel dates.
Flight Options: Finds real flight details, including prices and layovers.
Hotel Recommendations: Suggests hotels with ratings and prices across different budgets.
🤖 Multi-Agent Architecture: Utilizes a team of specialized AI agents that work together, each handling a specific task (research, flights, hotels, etc.).
💬 Interactive UI: A simple and beautiful user interface built with Streamlit.
🛠️ How It Works: The Multi-Agent Architecture
This project is built on the concept of agentic AI, where different AI agents collaborate to solve a complex problem. The entire workflow is managed by LangGraph, creating a robust and stateful execution graph.
The core of the application is a graph where each node is a specialized agent (a "worker") and a supervisor agent orchestrates the flow.
code
Mermaid
graph TD
    A[User Input via Streamlit UI] --> B{Supervisor Agent};
    B --> C{Decide Next Step};
    C --> D[Research Agent <br> (Visa, general info)];
    C --> E[Flight Agent <br> (Finds flights)];
    C --> F[Weather Agent <br> (Gets forecast)];
    C --> G[Hotel Agent <br> (Finds hotels)];
    C --> H[Activities Agent <br> (Suggests things to do)];
    
    subgraph Worker Agents
        D; E; F; G; H;
    end

    D --> B;
    E --> B;
    F --> B;
    G --> B;
    H --> B;

    C --> I[Itinerary Agent <br> (Synthesizes all data)];
    I --> J[✅ Final Plan];
    J --> K[Display in Streamlit];

    style A fill:#FF4B4B,stroke:#333,stroke-width:2px
    style K fill:#FF4B4B,stroke:#333,stroke-width:2px
    style B fill:#0068C9,stroke:#333,stroke-width:2px,color:#fff
    style I fill:#2E8B57,stroke:#333,stroke-width:2px,color:#fff
User Input: The user provides trip details through the Streamlit interface.
Supervisor Agent: This is the "team lead." It maintains the current state of the plan (what information has been gathered, what is missing) and decides which agent to call next.
Specialist Agents: Each worker agent has a specific tool and responsibility:
research_node: Uses Google Search to find visa information.
flight_node: Uses the SerpApi Flight Search tool.
hotel_node: Uses the SerpApi Hotel Search tool.
And so on for weather and activities.
Stateful Execution: After each agent completes its task, it updates the shared state, and control returns to the supervisor.
Itinerary Agent: Once the supervisor determines that all necessary information has been collected, it calls the final agent. This agent reviews all the gathered data (flights, hotels, weather, etc.) and uses its LLM capabilities to write a cohesive, day-by-day itinerary.
Final Output: The formatted itinerary is passed back to the Streamlit UI for the user to see.
🚀 Tech Stack
Orchestration: LangGraph for building stateful, multi-agent applications.
LLM: Google Gemini Pro for reasoning, planning, and content generation.
Tools & APIs: SerpApi for integrating Google Search, Flights, and Hotels APIs.
Frontend: Streamlit for creating the interactive web application.
Deployment: Streamlit Cloud for easy hosting and sharing.
Local Setup and Installation
1. Clone the Repository
code
Bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
2. Create a Virtual Environment
It's highly recommended to use a virtual environment to manage dependencies.
code
Bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
3. Install Dependencies
Create a requirements.txt file with the necessary libraries:```txt
streamlit
langgraph
langchain-google-genai
google-search-results
python-dotenv
Add any other libraries you use
code
Code
Then install them:
```bash
pip install -r requirements.txt
4. Set Up Environment Variables
You will need API keys for Google Gemini and SerpApi.
Create a file named .env in the root of your project and add your keys:
code
Code
# .env file
GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
SERPAPI_API_KEY="YOUR_SERPAPI_API_KEY"
5. Run the Application
code
Bash
streamlit run app.py
The application should now be running locally in your browser!
☁️ Deployment on Streamlit Cloud
Push your code to a GitHub repository.
Sign up or log in to Streamlit Cloud.
Click "New app" and connect your GitHub repository.
Before deploying, go to the "Advanced settings".
In the "Secrets" section, add your API keys. This is the secure way to handle them in the cloud.
code
Toml
# Streamlit Cloud Secrets (secrets.toml format)
GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
SERPAPI_API_KEY="YOUR_SERPAPI_API_KEY"
Click "Deploy!" and your app will be live.
🔮 Future Improvements

User Authentication: Allow users to save and view their past trip itineraries.

Budgeting Tools: Add a feature to track estimated costs for the trip.

Interactive Map: Visualize the itinerary on a map with pins for hotels and activities.

More Tools: Integrate agents for booking rental cars or finding local restaurants.
📜 License
This project is licensed under the MIT License. See the LICENSE file for details.
Use Arrow Up and Arrow Down to select a turn, Enter to jump to it, and Escape to return to the chat.
