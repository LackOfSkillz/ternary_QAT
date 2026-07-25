# Held-Out Eval - Automated Summary (Dispatch 30H)

**PROVISIONAL. Final human conclusions deferred until Gary's blind review is imported and unblinded.**

## By model arm (packet_adherence / prose_quality, 1-5)
| arm | packet_adherence | prose_quality |
|---|---|---|
| frozen_base | 3.409 | 3.647 |
| atomic_packet_sft | 3.591 | 3.672 |
| compositional_packet_sft | 3.773 | 3.692 |

## By prompt condition
| condition | packet_adherence | prose_quality |
|---|---|---|
| atomic_packet | 3.364 | 3.599 |
| compositional_packet | 3.818 | 3.741 |

## model x prompt interaction
| cell | packet_adherence | prose_quality | prov. structural high |
|---|---|---|---|
| frozen_base|atomic_packet | 3.091 | 3.515 | 1 |
| frozen_base|compositional_packet | 3.727 | 3.778 | 7 |
| atomic_packet_sft|atomic_packet | 3.455 | 3.697 | 1 |
| atomic_packet_sft|compositional_packet | 3.727 | 3.647 | 6 |
| compositional_packet_sft|atomic_packet | 3.545 | 3.586 | 1 |
| compositional_packet_sft|compositional_packet | 4 | 3.798 | 7 |

## Primary comparisons (right - left; +adherence favors right)
| comparison | adherence delta | prose delta | structural-high delta |
|---|---|---|---|
| training effect (atomic prompt) (frozen_base|atomic_packet vs atomic_packet_sft|atomic_packet) | 0.364 | 0.182 | 0 |
| training effect (compositional prompt) (frozen_base|compositional_packet vs compositional_packet_sft|compositional_packet) | 0.273 | 0.02 | 0 |
| prompt-format effect (atomic model) (atomic_packet_sft|atomic_packet vs atomic_packet_sft|compositional_packet) | 0.272 | -0.05 | 5 |
| prompt-format effect (compositional model) (compositional_packet_sft|atomic_packet vs compositional_packet_sft|compositional_packet) | 0.455 | 0.212 | 6 |
| training-format effect (compositional prompt) (atomic_packet_sft|compositional_packet vs compositional_packet_sft|compositional_packet) | 0.273 | 0.151 | 1 |
| training-format effect (atomic prompt) (atomic_packet_sft|atomic_packet vs compositional_packet_sft|atomic_packet) | 0.09 | -0.111 | 0 |

Conclusions are not drawn here; the blind human review governs final judgment.
