# BIM-agent

### Problem
BIM models in IFC are large and structurally complex, so direct querying is slow and requires deep expertise.

### Goal
Let users ask plain-English questions and receive fast, accurate answers.

### Approach
- Convert IFC data to lighter, query-friendly formats (SQL, JSON, Memgraph graph).

- Use an LLM to translate questions into Cypher/SQL queries.

- Return concise results to the user.

### Run agent
```python
python main.py \
  --query  "What is the perimeter of the entrance hall?" \
  --method <tool_based|builtin_context> \
  --db     <path/to/database.db>
```

- method

    - tool_based – the agent selects and executes auxiliary tools to generate a focused, usually more precise answer.

    - builtin_context – the agent receives an extended prompt where the database description is embedded directly.

- db – full or relative path to the target SQLite database file (e.g., data/building_ifc.db).

The results presented in this file: [тык](./tableConvert.com_fy2avz.pdf)