# Client - Server Trivia King: A Real-Time Networked Trivia Game
## Project Overview
This Trivia Game Server is a part of a client-server application designed to host trivia games. It manages player connections, broadcasts trivia questions, evaluates answers, and determines game outcomes based on player responses. The server uses UDP for broadcasting its presence to potential clients and TCP for handling game logic and player interactions.
The implementation of this project has written with python and can be run only locally on the same network.

## The Server screen:
![image](https://github.com/AyeletHashahar/Server-Client-trivia-contest-game/assets/167331530/bc8c7b9f-cf05-4cf6-96f7-9b3b34760423)

## The Client screen:
![image](https://github.com/AyeletHashahar/Server-Client-trivia-contest-game/assets/167331530/bc25448b-bfc7-4457-aa8c-9044e78bdf38)


## Features:
* **Multiplayer Gameplay**: Players connect to a central server using TCP/IP, engaging in a series of trivia rounds.
  
* **Dynamic Questioning**: Each game round presents a random trivia fact, requiring a true or false answer.
  
* **Immediate Feedback**: The server evaluates answers in real-time, instantly determining if a player's response is correct or incorrect.
  
* **Robust Server Handling**: The server manages multiple clients simultaneously, efficiently handling connections, disconnections, and data transmission.
  
* **Customizable Client-Server Interaction**: Includes a bot mode for automated responses, enhancing testing and gameplay variety.
 
* **Engaging User Interface**: Utilizes ANSI color coding for messages, making the game sessions vibrant and easy to read.
  
* **Comprehensive Game Statistics**: At the end of each game, the server broadcasts a summary and interesting statistics about the game session.
  
## How It Works:

1.**Server Broadcast**: The server begins by broadcasting offers over UDP to potential players every second.
   
2.**Client Connection**: Players receive these offers and connect over TCP, sending their names to the server.

3.**Gameplay***: The server sends a trivia question to all players, who submit their answers back to the server. Correct answers may immediately win the round or lead to disqualification on incorrect attempts.

4.**Round Continuation**: If no one answers correctly, or all players are disqualified, the server selects a new trivia question, continuing the excitement.

## Technical Architecture:
* The client is designed as a single-threaded application with states for searching, connecting, and gameplay.
  
* The server is multi-threaded, handling network communication, player management, and game logic.
  
* Packet formats are precisely defined for both UDP announcements and TCP communication, ensuring reliable data handling.

## Getting Started
### Prerequisites
* Python 3.x installed on your server machine.
* Basic knowledge of Python programming.
* Understanding of TCP/UDP networking concepts.
### Installation
1. Clone the repository:
   *git clone [https://your-repository-url.git](https://github.com/AyeletHashahar/Server-Client-trivia-contest-game/tree/main)*
   
2. Navigate to the project directory:
   *cd trivia-game-server*

3. Run the server:
   *python server.py*
   
## Usage
Start the server by executing **python server.py**. Once running, it will begin broadcasting its presence via UDP and listen for incoming TCP connections from clients wanting to participate in the trivia game.

Clients must be designed to listen for the server's UDP broadcasts, connect via TCP, and interact with the game logic as implemented on the server.

## Contact
* Ayelet Hashahar Cohen - www.linkedin.com/in/ayelet-hashahar-cohen
* Tzuf lahan - www.linkedin.com/in/tzuf-lahan-962b76233

Project Link: https://github.com/AyeletHashahar/Server-Client-trivia-contest-game/tree/main
