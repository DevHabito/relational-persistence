# RP-U004 — What repair algorithms already exist?

**Reading note:** 3 November 2026  
**Research lead:** Felipe Gianini Romero  
**Status:** Literature context for the frozen [RP-U004-P01 protocol](../preregistration/RP-U004-P01.md), not an experimental result or an exhaustive novelty review.

I should not treat the ability to restore a path, to preserve two vertex-disjoint routes, or to look ahead one repair step as an invention. The following publications already address network recovery, service continuity, scheduling optimization and the costs of heuristic decisions. Their systems and targets differ from my finite Boolean graph benchmark.

## Earlier methods and what they establish

**Fuyu Hu and colleagues (2016).** *Recovery of infrastructure networks after localised attacks*, *Scientific Reports*, volume 6, article 24522. DOI: [10.1038/srep24522](https://doi.org/10.1038/srep24522). Published in 2016. The authors compare greedy and local restoration heuristics after localized damage. Their comparison recognizes that selecting the best immediate edge does not guarantee the best complete repair sequence. This is an already-known limitation of myopic decisions. Their network-function measures are not identical to my specified F1/F2 Boolean outputs.

**Novella Bartolini, Stefano Ciavarella, Thomas F. La Porta and Simone Silvestri (2017).** *On Critical Service Recovery After Massive Network Failures*, *IEEE/ACM Transactions on Networking*. DOI: [10.1109/TNET.2017.2688330](https://doi.org/10.1109/TNET.2017.2688330). [Institutional record](https://research.uniroma1.it/pubblicazioni/39753). Critical-service recovery can be formulated as a constrained optimization problem, with heuristics for deciding what to restore. I cannot claim that choosing functional rather than structural metrics is new.

**Igor Averbakh and Jordi Pereira (2018).** *Lateness Minimization in Pairwise Connectivity Restoration Problems*, *INFORMS Journal on Computing*, 30(3), 522–538. DOI: [10.1287/ijoc.2017.0796](https://doi.org/10.1287/ijoc.2017.0796). Repair ordering and the time at which particular vertex pairs reconnect have been studied directly. Aggregate terminal connection uptime in RP-U004 is a simplified relative of this larger optimization problem.

**Fenghua Wang, Hale Cetinay, Zhidong He, Le Liu, Piet Van Mieghem and Robert E. Kooij (17 October 2023).** *Recovering Power Grids Using Strategies Based on Network Metrics and Greedy Algorithms*, *Entropy* 25(10), article 1455. DOI: [10.3390/e25101455](https://doi.org/10.3390/e25101455). [PubMed record](https://pubmed.ncbi.nlm.nih.gov/37895578/). The authors compare 13 restoration strategies, explicitly including greedy and **two-step greedy** methods, using a DC power-flow model and benchmark electricity networks. This is strong evidence that the strategy class itself is **not novel**. Their empirical findings about power networks cannot be transplanted to my synthetic F1/F2 graph without a defined physical model.

**Abigail J. Crocker and Stephen D. Boyles (23 April 2025 online).** *Heuristic Selection in Disaster Recovery Sequencing*, *Journal of Infrastructure Systems* 31(3). DOI: [10.1061/JITSE4.ISENG-2467](https://doi.org/10.1061/JITSE4.ISENG-2467). This paper compares eight algorithms for transportation repair sequencing, including bidirectional beam search and simulated annealing. More demanding search strategies are already part of the field. A small test of two-step lookahead is not an adequate replacement for comparing against that literature.

## What this changes in my experiment

RP-U003 previously showed a strict F1 gain against ASC and DEGREE, but **no aggregated F1 gain over GREEDY1**. That limitation is preserved; it helped determine the question posed by RP-U004, so RP-U004 cannot count as a blind confirmation of that previously seen pattern.

RP-U004 instead fixes a **new seven-vertex, eight-edge structural family**, pairs graphs by their full labeled degree vector, and makes all competitors read the **same complete subset-function table**. It tests a directional F2-aware lookahead comparison against an F2-aware greedy method; F1 remains a separately reported outcome. This is a test of how these particular heuristics behave in an entirely specified artificial problem, not a claim to have invented lookahead.

A shared function table equalizes access to the model's task information and the expensive precomputation. It **does not equalize decision CPU time**, and the published report must retain different lookup counts. No selected graph represents a physical electric grid, hospital, forest or spacecraft. There is no modeled power flow, material constraint, repair crew, actual deployment latency, environmental growth, measured service, or physical state variable.

Any future priority or generalization claim will need a separate novelty review, established baselines in the intended domain, and new measured outcomes. A passing finite result is evidence only about its frozen graph rules, not a physical law.

## Provenance note

I checked the cited publisher, institutional or PubMed records before adding these bibliographic entries. Exact publication dates are supplied where they could be verified; otherwise only the publication year is asserted. I have not independently replicated the calculations in the papers or examined every potentially competing method.

## Outcome of the preregistered comparison (added after the first run)

The first [RP-U004-P01 result](../results/RP-U004-P01.md) was archived on 3 November 2026 after the methods above had already been cited. It found a positive lookahead-versus-greedy difference **in a selected finite synthetic model**, with many ties and different lookup costs. It does not change the priority of any established recovery method. A subsequent audit also exposed a redundant comparison: prioritizing F1 over F2 or vice versa is equivalent for Boolean scores with F2 ⇒ F1. Any future study seeking a distinct objective-tradeoff effect needs non-nested objectives fixed before outcome inspection, not a reinterpretation of these scores.
