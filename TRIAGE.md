---
lab5_triage:
  image: ghcr.io/aaetheriss/itsm-svcdesk@sha256:b57196d1225a3e3a3f931dda3d9907620b5eb74f61820163890788e2fc1ef28b
  sarif_receipt: 447
---
<!-- ai-generated: 100% - ChatGPT generated the triage table and bake-off analysis from the receipted SARIF, revealed labels and published rules. -->
# Triage

Tabela obejmuje kazdy wynik skanerow poza katalogiem `lab5-canary/` w receipted SARIF oraz wszystkie aktywne wyjatki Trivy. Decyzje rozdzielaja naprawy wymagane przez bramki od znalezisk pozostawionych do raportowania i dalszego przegladu.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| semgrep | dockerfile.security.missing-user.missing-user | accept | Znalezienie raportowe przejrzano w Dockerfile; pozostaje widoczne do dalszej oceny, ale samo nie uzasadnia twardej bramki dla main. |
| trivy | runtime-base-image | fix | Obraz bazowy jest przypiety digestem, a pakiety systemowe sa aktualizowane przed zbudowaniem finalnego runtime. |
| trivy | pip-runtime-removal | fix | Narzedzia instalacyjne pip, setuptools i wheel sa usuwane z runtime, aby nie publikowac zbednych bibliotek buildowych. |

## Bake-off

Canary zawieral 10 oznaczonych defektow. Macierz nie jest rankingiem liczby znalezisk, lecz pomiarem kompromisu pomiedzy falszywymi alarmami a przeoczonymi defektami wedlug opublikowanej reguly dopasowania zakresu i klasy. Defekty sa celowo zwarte i rozpoznawalne, dlatego recall z tego zestawu jest raczej gornym oszacowaniem zachowania na prawdziwym kodzie produkcyjnym.

gitleaks: TP=2, FP=0, FN=8, precision=1.0000, recall=0.2000, F1=0.3333. Precision opisuje koszt przegladu alarmow tego detektora, a recall pokazuje, jaka czesc tego konkretnego zestawu seeded wykryl.

grype: TP=2, FP=0, FN=8, precision=1.0000, recall=0.2000, F1=0.3333. Precision opisuje koszt przegladu alarmow tego detektora, a recall pokazuje, jaka czesc tego konkretnego zestawu seeded wykryl.

osv-scanner: TP=2, FP=0, FN=8, precision=1.0000, recall=0.2000, F1=0.3333. Precision opisuje koszt przegladu alarmow tego detektora, a recall pokazuje, jaka czesc tego konkretnego zestawu seeded wykryl.

semgrep: TP=6, FP=1, FN=4, precision=0.8571, recall=0.6000, F1=0.7059. Precision opisuje koszt przegladu alarmow tego detektora, a recall pokazuje, jaka czesc tego konkretnego zestawu seeded wykryl.

trivy: TP=3, FP=0, FN=7, precision=1.0000, recall=0.3000, F1=0.4615. Precision opisuje koszt przegladu alarmow tego detektora, a recall pokazuje, jaka czesc tego konkretnego zestawu seeded wykryl.

Jako twarde bramki pozostawilabym gitleaks oraz Trivy, poniewaz ich alarmy odpowiadaja decyzjom, na ktore pipeline moze reagowac natychmiast: opublikowanemu sekretowi oraz podatnej zaleznosci lub obrazowi wymagajacemu naprawy. Status bramki wynika z rodzaju ryzyka, a nie z wygrania rankingu F1 na malym syntetycznym zbiorze. Grype, OSV-Scanner i Semgrep zachowalabym jako detektory raportujace, dopoki konkretne reguly nie wykaza stale wysokiej precyzji na naszym kodzie.

Najwazniejsze sa komorki FP i FN. Falszywe alarmy zuzywaja uwage i oslabiaja wiarygodnosc czerwonego builda, natomiast falszywe negatywy pokazuja, dlaczego pojedynczy skaner nie moze sam byc arbitrem. Dlatego zachowalabym dowod roznicowy z laboratorium: main musi pozostac zielony, canary musi uruchomic wlasciwe czerwone bramki, a kazdy wyjatek musi byc uzasadniony i ograniczony czasowo. Wynik dotyczy tego runu i tego zestawu, nie jest uniwersalna ocena narzedzi.
