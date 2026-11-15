from dataclasses import dataclass, field

@dataclass
class Agent:
    id: str
    name: str
    skills: set[str] = field(default_factory=set)
    allowed_actions: set[str] = field(default_factory=set)
    max_retries: int = 2

class AgentRegistry:
    def __init__(self, agents=None):
        self._agents = {a.id: a for a in (agents or [])}
    def register(self, agent): self._agents[agent.id] = agent
    def all(self): return list(self._agents.values())
    def get(self, agent_id): return self._agents.get(agent_id)
