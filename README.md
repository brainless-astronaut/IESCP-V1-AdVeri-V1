# AdVeri-V1
MAD 1 Project for IITM BS Data Science and Applications Degree

To understand the project, please refer to the report and presentation video available in the report. 

(P.S I am a really shy person, I was nervous in the video, so I apologise for any inconvenience caused.)

How to run the app.

Clone this repo usin the command:
git clone https://github.com/brainless-astronaut/AdVeri-V1.git

Navigate to the project folder:
cd AdVeri-V1/AdVeri

If you are using windows:

a. You can continue using windows to run the project.
    
    - Create a virtual environment (I am calling it .venv, for instance):
      python3 -m venv .venv
    
    - Activate .venv:
      .venv\Scripts\activate
    
    - Install dependecies:
      pip install -r requirements.txt
    
    - Run the app:
      python app.py

b. You can switch to WSL: 
     - WSL installation:
  
      Open command prompt and run as administrator:
  
      Type in the command:
        wsl --install

      This should install WSL into your system with Default Ubuntu Distro.
  
      Incase, you want a specific distro then type in:
        wsl --instal -d DIST 

      Wherein, DIST is is the name of the DIST you wish to install.

  WSL installation isn't needed if you are already using WSL/Linux/MAC

  The following commands is the one for running the project for all WSL, Linux, and MAC.
  
    - Create a virtual environment (I am calling it .venv, for instance):
      python3 -m venv .venv
  
    - Activate .venv:
      source .venv/bin/activate
      or
      . .venv/bin/activate (I prefer this one, its satisfactory to type in '. .' :))
   
    - Install dependencies:
      pip install -r requirements.txt
  
    - Run the app:
      python app.py

Have fun!

P.S This is my very first application, I went into this without prior experience. Please don't expect much, I have some errors, that I would correct in the near future! 

Thank you for reviewing my project!!

