# illusion_of_ethics

## 📁 Repository Structure

This project explores how large language models (LLMs) evaluate moral and immoral actions under varying contexts such as social norms, intentions, and outcomes. Below is the structure of the repository and description of each component:

```
├── code
│ └── Jupyter notebook with the experimental setup and evaluation logic.
│
├── data
│ └── prompts
│ ├── prompt generation files in JSONL format.
│
├── docs
│ └── documentation, analysis reports, and other references.
│
├── README.md
│ └── Main documentation file.
│
└── result
└── evaluation outputs, plots, or model results
```

## Prompt Descriptions

This dataset includes **10 distinct prompt sets** designed to probe how Large Language Models (LLMs) handle moral reasoning. The prompts are organized into four key categories based on experimental goals:

---

### 1. Choice of Action (2 Sets)

**Prompt Setup:**  
Each prompt presents a situation, an intention, and two possible actions — one moral and one immoral.

- **With Norm:** Includes an explicit social norm.
- **Without Norm:** No norm is provided.

**Objective:**  
To evaluate whether the presence of an explicit norm influences the LLM's decision, or if it relies on its own internalized moral framework.

---

### 2. Immoral Action Justification — Focus on Norm (2 Sets)

**Prompt Setup:**  
Each prompt presents an immoral action along with the situation and intention.

- **With Norm:** Norm is explicitly stated.
- **Without Norm:** No norm is included.

**Objective:**  
To assess if LLMs can justify immoral actions without knowing the outcome, and how the inclusion of a norm affects judgment.

---

### 3. Intention vs. Outcome Dilemma (2 Sets)

**Prompt Setup:**  
Each prompt presents:

- A **moral action** followed by an **immoral outcome**
- An **immoral action** followed by a **moral outcome**

**Objective:**  
To explore whether LLMs prioritize **intentions** or **outcomes** when evaluating the moral acceptability of actions in the absence of explicit instructions.

---

### 4. Prompt Injection (4 Sets)

**Prompt Setup:**  
These prompts are carefully worded to **steer** the LLM's moral judgment. Each scenario is designed to test the impact of prompt framing.

1. **Moral Action + Immoral Outcome:**  
   Prompt biases LLM to justify the action, disregarding the outcome.

2. **Moral Action + Immoral Outcome:**  
   Prompt biases LLM to reject the action due to the negative outcome.

3. **Immoral Action + Moral Outcome:**  
   Prompt encourages LLM to justify the action by focusing on the outcome.

4. **Immoral Action + Moral Outcome:**  
   Prompt biases LLM to reject the action regardless of the positive outcome.

**Objective:**  
To investigate the LLM’s susceptibility to **framing effects** in moral evaluations.
