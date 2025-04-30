# pip install tiktoken # (Falls noch nicht geschehen)
import tiktoken

# Kodierung für deine Modelle laden
encoding = tiktoken.get_encoding("cl100k_base")
# oder modellspezifisch:
# encoding = tiktoken.encoding_for_model("gpt-4-turbo-preview")

# Deinen gesamten Prompt-Text hier einfügen
prompt_text = """

Kontext: Ein Finanzinstitut mit folgendem Profil
Rechtsform: Aktiengesellschaft (AG)
Hauptsitz: Zürich, Schweiz
Gründung: 2005
Mitarbeiterzahl: ca. 850
Bilanzsumme: ca. 15 Mrd. CHF
Verwaltetes Vermögen (AuM): ca. 25 Mrd. CHF
Marktposition: Mittleres Finanzinstitut mit Fokus auf DACH-Region (Schweiz, Deutschland, Österreich). Spezialisiert auf nachhaltige Vermögensverwaltung für private und institutionelle Kunden sowie Finanzierungslösungen für KMU mit klaren ESG-Kriterien.

Geschäftsmodell & Kernaktivitäten:
1.  Nachhaltige Vermögensverwaltung: Entwicklung und Management von ESG-konformen Investmentfonds und individuellen Mandaten. Fokus auf Impact Investing und Themenfonds (Erneuerbare Energien, Kreislaufwirtschaft).
2.  KMU-Finanzierung: Bereitstellung von Krediten und Finanzierungslösungen für kleine und mittlere Unternehmen, die nachweislich Nachhaltigkeitsziele verfolgen oder sich in der Transformation befinden. Strenge ESG-Due-Diligence im Kreditprozess.
3.  ESG-Beratung: Beratung für institutionelle Kunden und KMU bei der Entwicklung und Umsetzung von Nachhaltigkeitsstrategien und ESG-Reporting.

Standorte: Zürich (HQ), Niederlassungen in Genf, Frankfurt am Main, Wien.

Bestehende ESG-Strategie & Ziele:
ASF AG hat sich öffentlich zu den Zielen des Pariser Klimaabkommens bekannt und strebt Klimaneutralität im eigenen Betrieb (Scope 1 & 2) bis 2035 an. Erste Erfahrungen mit TCFD-Reporting in Anlehnung. Mitgliedschaft bei UN PRI (Principles for Responsible Investment) seit 2015. Start der systematischen Erfassung von Scope 3 (finanzierte Emissionen) in 2023. Ziel ist die Entwicklung eines umfassenden Transitionplans bis Ende 2025 gemäss CSRD-Anforderungen und Best Practices.

Governance-Struktur für Nachhaltigkeit:
Nachhaltigkeitsausschuss auf Vorstandsebene (CSO als Mitglied).
Dediziertes ESG-Team (10 Mitarbeiter) verantwortlich für Strategieumsetzung, Reporting, Datenmanagement und Produktentwicklung.
Integration von ESG-Zielen in die variable Vergütung des Managements (eingeführt 2024).
 und dieser Portfolio-Analyse: Analyse des Investmentportfolios mit Fokus auf ESG-Risiken und -Chancen
Wichtigste Auffälligkeiten und Empfehlungen für den ESG-Transitionsplan:
Risiken:
1.	Hohe Klimarisiken in traditionellen Sektoren:
o	Global Oil Corp (INV004):
	Sektor: Öl & Gas (traditionell)
	Höchste finanzierte Emissionen im Portfolio (150.000 tCO₂e).
	Empfehlung: Aufgrund hoher Emissionen und strategischer Klimaziele (Reduktion Öl & Gas um 50% bis 2030) zeitnahes Engagement bzw. Prüfung einer mittelfristigen De-Investition.
2.	Hohe finanzierte Emissionen in spezifischen Assets:
o	Circular Plastics Fund (INV005):
	Hohe finanzierte Emissionen (12.000 tCO₂e).
	Empfehlung: Engeres Monitoring und aktives Engagement zur Verbesserung der Transparenz der ESG-Daten und Reduktion der Emissionen.
o	EcoTextil AG (INV003):
	Relativ hoher Emissionswert (2.500 tCO₂e) trotz kleinerem Investmentvolumen.
	Empfehlung: Vertiefte ESG-Due-Diligence und aktive Unterstützung bei der Transition.
3.	Datenverfügbarkeit & ESG-Scores:
o	Mögliche niedrige Datenqualität bei den hoch emittierenden Investments (insbesondere EcoTextil AG, Circular Plastics Fund, Global Oil Corp).
o	Empfehlung: Verstärktes Engagement zur Verbesserung der Datenqualität, insbesondere Scope-3-Emissionen, um Fortschritt präziser messen und steuern zu können.
Chancen:
1.	Investments mit klarem Nachhaltigkeitsprofil:
o	CleanEnergy Solutions GmbH (INV001):
	Sektor: Erneuerbare Energien (500 tCO₂e relativ gering)
	Positive ESG-Ausrichtung, klarer Beitrag zu Klimazielen.
	Empfehlung: Ausbau ähnlicher Investments im Bereich Erneuerbare Energien, Unterstützung bei Skalierungspotenzialen.
o	TechInnovate SE (INV002):
	Technologiebranche, niedrige Emissionen (150 tCO₂e).
	Potenzial für positive ESG-Impact-Lösungen (Software für Nachhaltigkeitsmanagement, digitale Lösungen zur Emissionsreduktion).
	Empfehlung: Prüfen weiterer Investitionen und Partnerschaften zur Verstärkung positiver ESG-Impulse.
Konzentration von finanzierten Emissionen:
•	Die emissionsintensivsten Positionen (v.a. Global Oil Corp, Circular Plastics Fund, EcoTextil AG) dominieren die Gesamtbilanz stark.
•	Empfehlung: Gezieltes Management dieser Positionen über Engagement, klar definierte Zwischenziele zur Emissionsreduktion oder strukturierten Ausstieg, um die Risikostruktur des Portfolios nachhaltig zu verbessern.
Diese Auffälligkeiten sollten im ESG-Transitionsplan priorisiert behandelt und mit den strategischen Klimazielen des Unternehmens (Reduktion der finanzierten Emissionen um 40% bis 2030, Netto-Null bis 2050) abgeglichen werden
. Frage an den Wissensgraphen: Welche spezifischen Anforderungen aus CSRD/ESRS und EU Taxonomie sind besonders relevant für solche Institute? Welche Benchmarks oder typischen Transition-Maßnahmen sind außerdem hoch relevant, werden in den indexierten Plänen anderer Finanzinstitute genannt?
strukturierte Liste  er gefunden best practices mit konkreten Beispielen




"""

num_tokens = len(encoding.encode(prompt_text))
print(f"Anzahl der Tokens im Prompt: {num_tokens}")