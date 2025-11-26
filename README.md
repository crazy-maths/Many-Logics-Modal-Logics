# Many-Logics Modal Structure Editor

A Python-based graphical tool for constructing, visualizing, and analyzing Many-Logics Modal Structures.

## Overview

Many-Logics Modal Structure Editor is an interactive GUI application designed for researchers, students, and developers working with many-logics modal structures. It provides tools to create custom lattices, build multi-world modal models, and evaluate modal formulas using both Up and Down interpretations supported in Many-Logics frameworks.

## Features

### 1. Algebraic Structure Creation

- **Custom Lattices**  
  Define elements and partial orders (`x ≤ y`) to construct arbitrary algebraic structures. The system automatically verifies lattice properties such as join/meet.

- **Filtered Lattices**  
  Designate a set of “true” values via Filters, used to determine formula satisfaction.

- **Many-Lattices**  
  Combine multiple complete sub-lattices to support Many-Logics Up/Down Interpretation.

- **Hasse Diagrams**  
  Visualize any lattice structure automatically using graph-based Hasse diagrams.

### 2. Modal Logic Modeling

- **World Creation**  
  Create modal worlds and associate each world with a specific complete sub-lattice. Assign truth values for propositional variables (`p, q, r, s`).

- **Kripke-Style Models**  
  Build accessibility graphs linking worlds through directed edges.

- **Model Visualization**  
  View the entire model as a directed graph showing worlds, accessibility relations, and the initial world.

### 3. Logic Evaluation & Analysis

- **Formula Parser**  
  Supports modal (`□`, `◇`) and boolean (`¬`, `∧`, `∨`, `→`, `↔`) operators.

- **Dual Interpretation Modes**  
  Switch between Up Interpretation and Down Interpretation to observe semantic differences between logic projections.

- **Satisfaction Checking**  
  Evaluate whether a formula’s truth value falls within the Filter of the lattice assigned to a world.

- **Model-Wide Validity**  
  Verify formula validity across all worlds in a model with one click.

## Installation

### Requirements

- Python 3.8 or higher

### Install Dependencies

```bash
pip install PyQt6 networkx matplotlib
```

## How to Run

Navigate to the project directory and execute the main application script:

```bash
python app.py
```

## Contact

Created by Rodrigo Alves (rodrigoalves@ua.pt)  
Feel free to reach out with questions or suggestions.
