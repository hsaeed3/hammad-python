# Cookbook - *Agents*

The `hammad` library takes inspiration heavily from `pydantic-ai`'s definition of agents. "*Agentic behavior*" as a concept is split into two modules:

- `hammad.genai.agents` : Single, Core Agentic Behavior
- `hammad.genai.graphs` : Multi-Agent Orchestration

## Defining An *Agent*

Creating an agent is incredibly simple, as with most resources within this
ecosystem, objects are typed very *literally*. Agents within `hammad.genai` implement **4** special functionalities:

- **Tool Use & Execution** : Agents can use tools to perform actions.
- **Structured Outputs** : Agents can generate structured outputs through the use of `instructor`.
- ***Context*** : A specialized object that can be read by agents as
context as well as dynamically and automatically updated by them using various strategies.
- **Hooks** : Agents can be configured to run hooks before and after each step of the agent's execution. (Tool Use, Context Updates, Final Output..)

At the very minimum, agents come *read-to-go* out of the box:

```python
from hammad.genai import Agent

agent = Agent()
```