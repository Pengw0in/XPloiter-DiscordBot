## 🕵️‍♂️ Xploiters CTF Bot

A lightweight Discord bot for the **Xploiters** team that automatically posts upcoming **CTF (Capture The Flag)** events from [CTFtime.org](https://ctftime.org).

### What It Does

- Posts a daily update of CTFs happening in the next 2 days  
- Shows:
  - CTF name and link  
  - Duration (start → end)  
  - Type (online / on-site)  
  - Organizer name  
  - Logo (if available)

###  Notes
- Uses the official CTFtime API
- Built with discord.py and aiohttp
- Handles API errors and skips if no events found
