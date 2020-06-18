import unittest
import requests
import evaluate as evaluate
import locate as locate

class Test(unittest.TestCase):
    def test_kwh_to_co2(self):
        process_kwh = 0.1
        year = 2016
        printToScreen = False

        # US locations
        breakdown = [5.868023799, 1.321624392, 66.17474207, 26.63395815] # [coal, oil, gas, low carbon]
        location = "Massachusetts"
        emission, state_emission = evaluate.emissions(process_kwh, breakdown, location, year, printToScreen)
        self.assertAlmostEqual(emission, 5.615832693, places=4)
        self.assertEqual(state_emission, 821.327)

        # Unknown and international location
        breakdown = [10, 20, 30, 40] # [coal, petroleum, gas, low carbon]
        location = "New Zealand"
        year = 2016
        printToScreen = False
        emission, state_emission = evaluate.emissions(process_kwh, breakdown, location, year, printToScreen)
        self.assertAlmostEqual(emission, 0.05084898172, places=4)
        self.assertEqual(state_emission, 0)

    def test_ip_to_location(self):
        printToScreen = False
        geo = requests.get("https://get.geojs.io/v1/ip/geo/165.82.47.11.json").json()
        self.assertEqual(locate.get(printToScreen, geo), "Pennsylvania")

    def test_get_local_energy_mix(self):
        year = "2016"
        # US locations
        location = "Pennsylvania"
        self.assertAlmostEqual(evaluate.energy_mix(location, year)[0], 25.4209872)
        self.assertAlmostEqual(evaluate.energy_mix(location, year)[1], 0.1686522923)
        self.assertAlmostEqual(evaluate.energy_mix(location, year)[2], 31.640982)
        self.assertAlmostEqual(evaluate.energy_mix(location, year)[3], 42.51657052)

        # Unknown or international locations
        location = "Unknown"
        self.assertAlmostEqual(evaluate.energy_mix((location, year)[0], 0.1434624948)
        self.assertAlmostEqual(evaluate.energy_mix(location, year)[1], 0.3945439942)
        self.assertAlmostEqual(evaluate.energy_mix(location, year)[2], 0.2864046947)
        self.assertAlmostEqual(evaluate.energy_mix(location, year)[3], 0.1755888163)

    def test_emissions_comparison(self):
        process_kwh = 0.1
        locations = ["New Zealand"]
        year = 2016
        default_location = False
        printToScreen = False
        comparison_values = emissions_comparison(process_kwh, locations, year, default_location, printToScreen)
        self.assertTupleEqual(comparison_values, [("New Zealand", 0.05084898172)])

    def test_old_emissions_comparison(self):
        process_kwh = 0.1
        year = 2016
        default_location = True
        printToScreen = False
        default_emissions = old_emissions_comparison(process_kwh, year, default_location, printToScreen)
        self.assertTupleEqual(default_emissions, [("Mongolia", 0.09236681492), \
        ("Korea, South", 0.07543616588), ("Bhutan", 0.01050256992), ("Kosovo", 0.09435875313), \
        ("Ukraine", 0.06592509932), ("Iceland", 0.01697882193), ("Wyoming", 8.680138), \
        ("Mississippi", 6.775571984), ("Vermont", 0.02482178507)])


if __name__ == '__main__':
    unittest.main()
