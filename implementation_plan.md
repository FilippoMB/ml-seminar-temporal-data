# Temporal Deep Learning Presentation Upgrade

## Summary
Improve `presentation_temporal.html` into a polished 30-minute Reveal.js lecture for physics/CS remote-sensing researchers. Keep the lecture strictly temporal, keep the electricity example as an accessible stepping stone, and do not add spatio-temporal or foundation-model sections.

The revised narrative is:
1. Problem framing and remote-sensing motivation.
2. Fixed windows and MLPs.
3. Recurrent state models.
4. Reservoir computing as low-training recurrence.
5. Temporal convolutions.
6. Attention and transformers.
7. State space models and Mamba.
8. Remote-sensing examples.
9. Architecture map and takeaways.

## Key Changes
- Remove slide-visible planning metadata such as "30 minutes" and "20-25 slides".
- Keep the deck to about 26-27 slides including references.
- Add one compact modern-methods section on state space models:
  - Explain SSMs from the physics/control view: latent state, input, output, discretized dynamics.
  - Position S4/Mamba as recurrent intuition with scan-style efficiency and long-context scaling.
  - Add SSM/Mamba to the final architecture comparison table.
- Tighten reservoir computing:
  - Present it as an Echo State Network/readout method useful when labels are limited or recurrent training is expensive.
  - Merge redundant readout/tuning material where possible.
- Strengthen remote-sensing relevance:
  - Move satellite image time series motivation earlier.
  - Weave examples through the methods: phenology/crop type classification for RNN/TCN/attention, cloud gaps and irregular acquisition for masking/attention, flood before-after as temporal change detection.
  - Keep the electricity-demand example as the non-remote-sensing bridge from tabular windows to neural temporal models.

## Visual Direction
- Use a clean technical lecture style: modern sans-serif typography, restrained remote-sensing palette, stronger spacing hierarchy, consistent captions, and stable image/diagram sizing.
- Avoid glassmorphism, decorative gradients, and extra micro-animations.
- Improve inline SVG diagrams with consistent colors, labels, arrows, and alignment.
- Add one inline SVG for SSM/Mamba showing input sequence, selective state update/scan, and output sequence.
- Revise the architecture map to compare memory mechanisms: explicit window, recurrent state, random reservoir, temporal filter, attention, and state space scan.

## References To Use
- Benidis et al., "Deep Learning for Time Series Forecasting", ACM Computing Surveys, 2022.
- Jaeger, "The echo state approach to analysing and training recurrent neural networks", 2001.
- Bai, Kolter, and Koltun, "An Empirical Evaluation of Generic Convolutional and Recurrent Networks for Sequence Modeling", 2018.
- Vaswani et al., "Attention Is All You Need", 2017.
- Gu et al., "Efficiently Modeling Long Sequences with Structured State Spaces", 2021.
- Gu and Dao, "Mamba: Linear-Time Sequence Modeling with Selective State Spaces", 2023.
- Pelletier, Webb, and Petitjean, "Temporal Convolutional Neural Network for the Classification of Satellite Image Time Series", Remote Sensing, 2019.
- Garnot et al., "Satellite Image Time Series Classification with Pixel-Set Encoders and Temporal Self-Attention", CVPR, 2020.

## Verification Plan
- Load the deck from localhost and confirm Reveal initializes with no browser console errors.
- Use Codex Browser checks for title slide, architecture slides, EO example slides, SSM slide, comparison table, and references.
- If in-app screenshot capture times out, use browser DOM/log verification and local screenshot fallback for visual QA.
- Check that local media are referenced correctly and that no slide obviously overflows the 1366x768 Reveal canvas.
- Verify final slide count and flow support a 30-minute lecture without rushing.
