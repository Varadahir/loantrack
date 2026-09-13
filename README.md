\# LoanTrack



LoanTrack is a three-tier loan tracking application consisting of:



\- Frontend: Nginx serving the web UI

\- Backend: FastAPI REST API

\- Database: PostgreSQL



The application is designed to run locally using Docker Compose and Kubernetes.



\---



\## Architecture



```text

&#x20;                        Browser

&#x20;                           |

&#x20;                           v

&#x20;                 +-------------------+

&#x20;                 |     Frontend      |

&#x20;                 |      Nginx        |

&#x20;                 |     :8080         |

&#x20;                 +---------+---------+

&#x20;                           |

&#x20;                        HTTP /api

&#x20;                           |

&#x20;                           v

&#x20;                 +-------------------+

&#x20;                 |      Backend      |

&#x20;                 |      FastAPI      |

&#x20;                 |      :8000        |

&#x20;                 +---------+---------+

&#x20;                           |

&#x20;                      PostgreSQL

&#x20;                      :5432

&#x20;                           |

&#x20;                           v

&#x20;                 +-------------------+

&#x20;                 |     PostgreSQL    |

&#x20;                 |       loans       |

&#x20;                 +-------------------+



Docker Compose:

&#x20; frontend -> backend -> db

&#x20; db uses named persistent volume



Kubernetes:

&#x20; frontend -> NodePort

&#x20; backend  -> ClusterIP

&#x20; postgres -> ClusterIP + StatefulSet + PVC

