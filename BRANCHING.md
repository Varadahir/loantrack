\# LoanTrack Git Branching Strategy



\## Branches



LoanTrack uses a simple feature-based Git workflow.



\- `main` - stable, deployable project state.

\- `develop` - integration branch for completed features.

\- `feature/\*` - individual feature or assignment-part branches.



Current feature branches:



\- `feature/application-foundation`

\- `feature/docker-compose`

\- `feature/kubernetes`



\## Development Flow



Each feature branch is created from `develop`.



```text

main

&#x20; │

&#x20; └── develop

&#x20;      │

&#x20;      ├── feature/application-foundation

&#x20;      │

&#x20;      ├── feature/docker-compose

&#x20;      │

&#x20;      └── feature/kubernetes

