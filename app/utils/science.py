import random
import time

SCIENCE_FACTS = [
    {
        "slug": "how-clouds-form",
        "title": "How Clouds Form",
        "category": "Basics",
        "category_class": "text-primary",
        "description": "Understanding the process of condensation and nucleation in the atmosphere.",
        "image": "https://images.unsplash.com/photo-1594156596782-fa8205b1f189?w=600&q=80",
        "content": """
            <p>Clouds are visible accumulations of tiny water droplets or ice crystals in the Earth's atmosphere.</p>
            <h4>The Process</h4>
            <p>Clouds form when water vapor, an invisible gas, turns into liquid water droplets. This process is called <strong>condensation</strong>.</p>
            <p>For condensation to occur, the air must be saturated with water vapor. This usually happens when warm air rises, expands, and cools. Cool air can hold less water vapor than warm air, so as the air cools, some of the vapor condenses onto tiny particles floating in the air called <strong>Cloud Condensation Nuclei (CCN)</strong>.</p>
            <p>These nuclei can be dust, smoke, salt from the ocean, or pollution. Without these particles, clouds would have a very hard time forming!</p>
        """
    },
    {
        "slug": "tornado-genesis",
        "title": "Tornado Genesis",
        "category": "Severe Weather",
        "category_class": "text-danger",
        "description": "What conditions are necessary for a supercell thunderstorm to produce a tornado?",
        "image": "https://images.unsplash.com/photo-1527482797697-8795b05a13fe?w=600&q=80",
        "content": """
            <p>A tornado is a violently rotating column of air that is in contact with both the surface of the Earth and a cumulonimbus cloud.</p>
            <h4>Supercells</h4>
            <p>Most strong tornadoes form from a specific type of thunderstorm called a <strong>supercell</strong>. Supercells contain a deep, persistent rotating updraft called a mesocyclone.</p>
            <p>For a tornado to form, specific conditions are needed:</p>
            <ul>
                <li><strong>Instability:</strong> Warm, moist air near the ground and cooler dry air aloft.</li>
                <li><strong>Wind Shear:</strong> Change in wind speed and direction with height.</li>
            </ul>
            <p>When these conditions align, the rotating air column can tighten and accelerate, eventually reaching the ground as a tornado.</p>
        """
    },
    {
        "slug": "greenhouse-effect",
        "title": "The Greenhouse Effect",
        "category": "Climate",
        "category_class": "text-success",
        "description": "A deep dive into how greenhouse gases trap heat and warm our planet.",
        "image": "https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=600&q=80",
        "content": """
            <p>The greenhouse effect is a natural process that warms the Earth's surface.</p>
            <h4>How it Works</h4>
            <p>When the Sun's energy reaches the Earth's atmosphere, some of it is reflected back to space and the rest is absorbed and re-radiated by greenhouse gases.</p>
            <p>Greenhouse gases include water vapor, carbon dioxide, methane, nitrous oxide, and ozone. Without this natural greenhouse effect, Earth's average temperature would be about -18°C (0°F), instead of the comfortable 15°C (59°F) it is today.</p>
            <p>However, human activities are significantly increasing the concentration of these gases, intensifying the greenhouse effect and leading to global warming.</p>
        """
    },
    {
        "slug": "enso",
        "title": "El Niño Southern Oscillation",
        "category": "Climate",
        "category_class": "text-success",
        "description": "How warming ocean waters in the Pacific affect global weather patterns.",
        "image": "https://images.unsplash.com/photo-1560264280-88b68371db39?w=600&q=80",
        "content": """
            <p>The El Niño-Southern Oscillation (ENSO) is a recurring climate pattern involving changes in the temperature of waters in the central and eastern tropical Pacific Ocean.</p>
            <h4>El Niño vs. La Niña</h4>
            <ul>
                <li><strong>El Niño:</strong> Warming of the ocean surface, or above-average sea surface temperatures (SST), in the central and eastern tropical Pacific Ocean. It often leads to wetter conditions in the southern U.S. and warmer, drier conditions in the north.</li>
                <li><strong>La Niña:</strong> Cooling of the ocean surface, or below-average SSTs, in the central and eastern tropical Pacific Ocean. Its effects are generally the opposite of El Niño.</li>
            </ul>
        """
    },
    {
        "slug": "coriolis-effect",
        "title": "The Coriolis Effect",
        "category": "Physics",
        "category_class": "text-info",
        "description": "Why storms spin counter-clockwise in the Northern Hemisphere.",
        "image": "https://images.unsplash.com/photo-1454789548728-85d2696cf661?w=600&q=80",
        "content": """
            <p>The Coriolis effect creates an apparent deflection of the path of an object that moves within a rotating coordinate system.</p>
            <h4>In Meteorology</h4>
            <p>Because the Earth rotates, circulating air is deflected to the right in the Northern Hemisphere and to the left in the Southern Hemisphere.</p>
            <p>This deflection is a major factor in explaining why winds blow counter-clockwise around low pressure systems in the Northern Hemisphere and clockwise in the Southern Hemisphere.</p>
        """
    },
    {
        "slug": "atmospheric-rivers",
        "title": "Atmospheric Rivers",
        "category": "Hydrology",
        "category_class": "text-primary",
        "description": "Rivers in the sky that transport massive amounts of water vapor.",
        "image": "https://images.unsplash.com/photo-1561553873-e8491a564fd0?w=600&q=80",
        "content": """
            <p>Atmospheric rivers are relatively long, narrow regions in the atmosphere, like rivers in the sky, that transport most of the water vapor outside of the tropics.</p>
            <h4>Impact</h4>
            <p>When atmospheric rivers make landfall, they often release this water vapor in the form of rain or snow. They are responsible for a significant percentage of the precipitation in western North America.</p>
            <p>While they provide crucial water, strong atmospheric rivers can cause devastating floods and landslides.</p>
        """
    },
    {
        "slug": "jet-streams",
        "title": "Jet Streams",
        "category": "Basics",
        "category_class": "text-primary",
        "description": "Fast flowing, narrow air currents that drive weather systems.",
        "image": "https://images.unsplash.com/photo-1525609004556-c46c7d6cf023?w=600&q=80",
        "content": """
            <p>Jet streams are fast flowing, narrow, meandering air currents in the atmospheres of some planets, including Earth.</p>
            <h4>Location</h4>
            <p>On Earth, the main jet streams are located near the altitude of the tropopause and are westerly winds (flowing west to east). Their paths involve meanders.</p>
            <h4>Influence</h4>
            <p>Jet streams play a key role in determining the weather because they usually separate colder air and warmer air. They push weather systems around the globe and can steer storms.</p>
        """
    },
    {
        "slug": "albedo-effect",
        "title": "Albedo Effect",
        "category": "Physics",
        "category_class": "text-info",
        "description": "How the reflectivity of Earth's surface impacts global temperature.",
        "image": "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=600&q=80",
        "content": """
            <p>Albedo is a measure of the reflectivity of a surface. It is the fraction of solar energy (shortwave radiation) reflected from the Earth back into space.</p>
            <h4>Examples</h4>
            <ul>
                <li><strong>High Albedo:</strong> Ice, snow, and clouds. They reflect most sunlight, keeping the surface cool.</li>
                <li><strong>Low Albedo:</strong> Oceans, forests, and asphalt. They absorb most sunlight, warming the surface.</li>
            </ul>
            <p>As ice melts due to warming, the surface exhibits lower albedo (ocean water instead of ice), which absorbs more heat, causing further melting in a positive feedback loop.</p>
        """
    },
    {
        "slug": "polar-vortex",
        "title": "Polar Vortex",
        "category": "Severe Weather",
        "category_class": "text-danger",
        "description": "The large area of low pressure and cold air surrounding Earth's poles.",
        "image": "https://images.unsplash.com/photo-1483664852095-d6cc6870705d?w=600&q=80",
        "content": """
            <p>The polar vortex is a large area of low pressure and cold air surrounding both of the Earth's poles. It always exists near the poles, but it weakens in summer and strengthens in winter.</p>
            <h4>Disruption</h4>
            <p>Sometimes, the polar vortex can become disrupted or split. When this happens, the cold air that is usually bottled up at the poles can spill southward into North America, Europe, and Asia, leading to extreme cold outbreaks.</p>
        """
    },
    {
        "slug": "monsoons",
        "title": "Monsoons",
        "category": "Seasonal",
        "category_class": "text-warning",
        "description": "Seasonal changes in atmospheric circulation and precipitation.",
        "image": "https://images.unsplash.com/photo-1519692933481-e162a57d6721?w=600&q=80",
        "content": """
            <p>A monsoon is a seasonal change in the direction of the prevailing, or strongest, winds of a region. Monsoons cause wet and dry seasons throughout much of the tropics.</p>
            <h4>Causes</h4>
            <p>Monsoons are caused by the temperature difference between the land and the ocean. In summer, the land warms up faster than the ocean, creating low pressure over the land that draws in moist ocean air (wet monsoon).</p>
        """
    },
    {
        "slug": "flash-floods",
        "title": "Flash Floods",
        "category": "Severe Weather",
        "category_class": "text-danger",
        "description": "Rapid flooding of low-lying areas: causes, dangers, and safety.",
        "image": "https://images.unsplash.com/photo-1524388373300-8809ff44ad7e?w=600&q=80",
        "content": """
            <p>A flash flood is a rapid flooding of low-lying areas: washes, rivers, dry lakes and depressions.</p>
            <h4>Causes</h4>
            <p>It may be caused by heavy rain associated with a severe thunderstorm, hurricane, tropical storm, or meltwater from ice or snow flowing over ice sheets or snowfields.</p>
            <h4>Danger</h4>
            <p>Flash floods are distinct from regular floods because they happen very quickly, often within 6 hours of the rain event, giving people very little time to evacuate.</p>
        """
    },
    {
        "slug": "heat-waves",
        "title": "Heat Waves",
        "category": "Extreme Events",
        "category_class": "text-danger",
        "description": "Prolonged periods of excessively hot weather and their health impacts.",
        "image": "https://images.unsplash.com/photo-1504386106331-3e4e71712b38?w=600&q=80",
        "content": """
            <p>A heat wave is a period of excessively hot weather, which may be accompanied by high humidity.</p>
            <h4>Definition</h4>
            <p>While definitions vary, a heat wave is generally measured relative to the usual weather in the area and relative to normal temperatures for the season.</p>
            <h4>High Pressure Domes</h4>
            <p>Heat waves often form when high pressure aloft (from 10,000–25,000 feet) strengthens and remains over a region for several days or weeks. This traps heat near the ground.</p>
        """
    }
]

def get_rotated_science_facts(limit=3):
    """
    Returns a list of science facts that rotates every 5 hours.
    """
    # 5 hours in seconds
    window_duration = 5 * 3600
    
    # Get current 5-hour window index
    current_window = int(time.time() // window_duration)
    
    # Seed random with this window index to ensure consistency for 5 hours
    # We use a localized random instance to avoid affecting global random state
    rng = random.Random(current_window)
    
    # Select 'limit' items
    return rng.sample(SCIENCE_FACTS, min(limit, len(SCIENCE_FACTS)))

def get_science_fact_by_slug(slug):
    """
    Returns a single science fact by its slug or None if not found.
    """
    for fact in SCIENCE_FACTS:
        if fact["slug"] == slug:
            return fact
    return None
