"""
========================================================
  Dynamic Pricing Optimization System
  Built with OOP: Encapsulation, Inheritance,
  Polymorphism, Abstraction, Singleton, Composition
========================================================
"""

import random
import time
from abc import ABC, abstractmethod
from datetime import datetime


# ─────────────────────────────────────────────
# PRICING STRATEGIES  (Abstraction + Polymorphism)
# ─────────────────────────────────────────────

class PricingStrategy(ABC):
    """Abstract base class for all pricing strategies."""

    @abstractmethod
    def calculate(self, product, market) -> float:
        pass


class SurgePricingStrategy(PricingStrategy):
    """Raises price sharply when demand exceeds a threshold."""

    def __init__(self, threshold: float = 70, surge_rate: float = 0.8):
        self.threshold = threshold
        self.surge_rate = surge_rate

    def calculate(self, product, market) -> float:
        if market.demand_score > self.threshold:
            factor = 1 + self.surge_rate * ((market.demand_score - self.threshold) / 100)
            return product.base_price * factor
        return product.base_price

    def __str__(self):
        return "SurgePricing"


class CompetitivePricingStrategy(PricingStrategy):
    """Undercuts competitors slightly based on pressure index."""

    def calculate(self, product, market) -> float:
        comp_factor = 1 - (market.competitor_pressure / 100) * 0.15
        return product.base_price * comp_factor

    def __str__(self):
        return "CompetitivePricing"


class DemandElasticityStrategy(PricingStrategy):
    """Scales price smoothly with demand elasticity coefficient."""

    def __init__(self, elasticity_coeff: float = 0.6):
        self.elasticity_coeff = elasticity_coeff

    def calculate(self, product, market) -> float:
        elasticity = 1 + self.elasticity_coeff * ((market.demand_score - 50) / 100)
        return product.base_price * elasticity

    def __str__(self):
        return "DemandElasticity"


# ─────────────────────────────────────────────
# MARKET STATE  (Encapsulation)
# ─────────────────────────────────────────────

class MarketState:
    """Holds the current market snapshot for one pricing cycle."""

    def __init__(self, demand_score, competitor_pressure, scarcity, urgency, season_factor):
        self.demand_score = round(demand_score, 2)
        self.competitor_pressure = round(competitor_pressure, 2)
        self.scarcity = scarcity
        self.urgency = urgency
        self.season_factor = season_factor

    def __str__(self):
        return (f"  Demand score       : {self.demand_score:.1f}/100\n"
                f"  Competitor pressure: {self.competitor_pressure:.1f}/100\n"
                f"  Scarcity           : {self.scarcity}/100\n"
                f"  Urgency            : {self.urgency}/100\n"
                f"  Season factor      : {self.season_factor:.2f}x")


# ─────────────────────────────────────────────
# MARKET ANALYZER  (Encapsulation)
# ─────────────────────────────────────────────

class MarketAnalyzer:
    """Analyzes raw market parameters and produces a MarketState."""

    def analyze(self, demand, competitor, inventory, urgency, season) -> MarketState:
        noise = lambda: random.uniform(-6, 6)
        return MarketState(
            demand_score=min(100, demand + noise()),
            competitor_pressure=max(0, min(100, competitor + noise() * 0.5)),
            scarcity=inventory,
            urgency=urgency,
            season_factor=season / 100
        )


# ─────────────────────────────────────────────
# CUSTOMER SEGMENTS  (Encapsulation)
# ─────────────────────────────────────────────

class CustomerSegment:
    """Models a buyer cohort and their price willingness."""

    def __init__(self, name: str, base_pct: float, sensitivity: float):
        self.name = name
        self.base_pct = base_pct      # share of market %
        self.sensitivity = sensitivity # 0=insensitive, 1=very sensitive

    def willingness(self, market: MarketState) -> float:
        """Returns willingness-to-pay multiplier for this segment."""
        adjustment = (market.demand_score - 50) * (1 - self.sensitivity) * 0.005
        return max(0.5, min(2.0, 1 + adjustment))

    def __str__(self):
        return f"{self.name} ({self.base_pct:.0f}% market share, sensitivity={self.sensitivity})"


# ─────────────────────────────────────────────
# PRODUCTS  (Inheritance + Polymorphism)
# ─────────────────────────────────────────────

class Product:
    """Base product class — holds price, strategy, and constraint logic."""

    def __init__(self, name: str, base_price: float, category: str):
        self.name = name
        self.base_price = base_price
        self.category = category
        self.current_price = base_price
        self._strategy: PricingStrategy = None

    def set_strategy(self, strategy: PricingStrategy):
        self._strategy = strategy

    def _apply_constraints(self, price: float, floor: float, cap: float) -> float:
        low  = self.base_price * floor
        high = self.base_price * cap
        return round(max(low, min(high, price)), 2)

    def get_optimal_price(self, market: MarketState, floor=0.7, cap=2.0) -> float:
        if self._strategy is None:
            return self.base_price
        raw = self._strategy.calculate(self, market)
        return self._apply_constraints(raw, floor, cap)

    def update_price(self, market: MarketState, floor=0.7, cap=2.0) -> float:
        old = self.current_price
        self.current_price = self.get_optimal_price(market, floor, cap)
        return old

    def __str__(self):
        return (f"{self.name:<28} [{self.category:<11}]  "
                f"base=${self.base_price:>8.2f}  "
                f"current=${self.current_price:>8.2f}  "
                f"strategy={self._strategy}")


class ElectronicsProduct(Product):
    """Electronics: includes tech-obsolescence decay each cycle."""

    def __init__(self, name, base_price):
        super().__init__(name, base_price, "Electronics")
        self._cycle = 0

    def get_optimal_price(self, market, floor=0.7, cap=2.0) -> float:
        self._cycle += 1
        raw = super().get_optimal_price(market, floor, cap)
        decay = 1 - 0.03 * (self._cycle % 5)   # depreciation every 5 cycles
        return self._apply_constraints(raw * decay, floor, cap)


class TravelProduct(Product):
    """Travel: seat scarcity drives additional markup."""

    def __init__(self, name, base_price):
        super().__init__(name, base_price, "Travel")

    def get_optimal_price(self, market, floor=0.7, cap=2.0) -> float:
        raw = super().get_optimal_price(market, floor, cap)
        scarcity_boost = 1 + 0.30 * (market.scarcity / 100)
        return self._apply_constraints(raw * scarcity_boost, floor, cap)


class GroceryProduct(Product):
    """Grocery: expiry urgency applies downward pressure."""

    def __init__(self, name, base_price):
        super().__init__(name, base_price, "Grocery")

    def get_optimal_price(self, market, floor=0.7, cap=2.0) -> float:
        raw = super().get_optimal_price(market, floor, cap)
        expiry_discount = 1 - 0.08 * (market.urgency / 100)
        return self._apply_constraints(raw * expiry_discount, floor, cap)


class SaaSProduct(Product):
    """SaaS subscription: stable pricing with minor competitor tracking."""

    def __init__(self, name, base_price):
        super().__init__(name, base_price, "SaaS")


# ─────────────────────────────────────────────
# PRICE LOGGER  (Singleton)
# ─────────────────────────────────────────────

class PriceLogger:
    """Singleton logger — one shared log across all engine cycles."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._logs = []
        return cls._instance

    @staticmethod
    def get_instance():
        return PriceLogger()

    def log(self, cycle, product_name, old_price, new_price, strategy):
        delta_pct = ((new_price - old_price) / old_price) * 100 if old_price else 0
        tag = "SURGE" if delta_pct > 1 else "DROP" if delta_pct < -1 else "ADJUST"
        entry = {
            "cycle"  : cycle,
            "time"   : datetime.now().strftime("%H:%M:%S"),
            "product": product_name,
            "old"    : old_price,
            "new"    : new_price,
            "delta"  : delta_pct,
            "tag"    : tag,
            "strategy": strategy
        }
        self._logs.append(entry)

    def get_logs(self):
        return list(self._logs)

    def print_recent(self, n=10):
        print(f"\n  {'Cycle':<6} {'Time':<10} {'Tag':<8} {'Product':<28} {'Old':>8} {'New':>8} {'Δ%':>7}  Strategy")
        print("  " + "─" * 90)
        for e in self._logs[-n:]:
            sign = "+" if e['delta'] >= 0 else ""
            print(f"  {e['cycle']:<6} {e['time']:<10} {e['tag']:<8} {e['product']:<28} "
                  f"${e['old']:>7.2f} ${e['new']:>7.2f} {sign}{e['delta']:>5.1f}%  {e['strategy']}")


# ─────────────────────────────────────────────
# PRICING ENGINE  (Composition + Controller)
# ─────────────────────────────────────────────

class PricingEngine:
    """
    Main controller — composes MarketAnalyzer, Products,
    Strategies, Segments, and Logger into one pricing loop.
    """

    def __init__(self):
        self.analyzer = MarketAnalyzer()
        self.logger   = PriceLogger.get_instance()
        self.cycle    = 0
        self.price_history = []        # (cycle, avg_index)
        self.strategy_counts = {"SurgePricing": 0, "CompetitivePricing": 0, "DemandElasticity": 0}

        # --- Build product catalog ---
        self.products = [
            self._make(ElectronicsProduct("Smartphone Pro",    599.00), SurgePricingStrategy(65, 0.5)),
            self._make(ElectronicsProduct("Laptop Ultra",      999.00), DemandElasticityStrategy(0.5)),
            self._make(TravelProduct    ("Flight SIN→NYC",     850.00), SurgePricingStrategy(60, 1.2)),
            self._make(TravelProduct    ("Hotel (3 nights)",   320.00), CompetitivePricingStrategy()),
            self._make(GroceryProduct   ("Organic Veggie Box",  45.00), DemandElasticityStrategy(0.3)),
            self._make(SaaSProduct      ("Analytics SaaS/mo",   29.00), CompetitivePricingStrategy()),
        ]

        # --- Customer segments ---
        self.segments = [
            CustomerSegment("Premium buyers",    30, sensitivity=0.1),
            CustomerSegment("Mid-market buyers", 45, sensitivity=0.5),
            CustomerSegment("Budget shoppers",   25, sensitivity=0.9),
        ]

    def _make(self, product, strategy):
        product.set_strategy(strategy)
        return product

    def run_cycle(self, demand=70, competitor=40, inventory=30, urgency=20,
                  season=100, floor=0.70, cap=2.0):
        self.cycle += 1
        market = self.analyzer.analyze(demand, competitor, inventory, urgency, season)

        print(f"\n{'═'*65}")
        print(f"  CYCLE {self.cycle}   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'═'*65}")
        print("\n  ── Market state ──")
        print(market)

        print(f"\n  ── Product pricing ──")
        print(f"  {'Product':<28} {'Category':<12} {'Base':>8} {'Old':>8} {'New':>8}  {'Δ%':>6}  Strategy")
        print("  " + "─" * 80)

        total_index = 0
        for p in self.products:
            old = p.update_price(market, floor, cap)
            new = p.current_price
            delta = ((new - old) / old) * 100
            sign = "+" if delta >= 0 else ""
            strat_name = str(p._strategy)
            self.strategy_counts[strat_name] = self.strategy_counts.get(strat_name, 0) + 1
            self.logger.log(self.cycle, p.name, old, new, strat_name)
            total_index += new / p.base_price
            print(f"  {p.name:<28} {p.category:<12} ${p.base_price:>7.2f} ${old:>7.2f} ${new:>7.2f}  {sign}{delta:>4.1f}%  {strat_name}")

        avg_index = total_index / len(self.products)
        self.price_history.append((self.cycle, round(avg_index, 3)))
        revenue_lift = (avg_index - 1) * 100

        print(f"\n  ── Segment willingness-to-pay ──")
        for seg in self.segments:
            wtp = seg.willingness(market)
            bar = "█" * int(wtp * 20)
            print(f"  {seg.name:<22}  WTP={wtp:.2f}x  {bar}")

        print(f"\n  ── Cycle summary ──")
        print(f"  Avg price index : {avg_index:.3f}x")
        print(f"  Revenue lift    : {'+' if revenue_lift >= 0 else ''}{revenue_lift:.1f}% vs static pricing")
        print(f"  Total cycles    : {self.cycle}")

        return avg_index, revenue_lift

    def print_price_history(self):
        print(f"\n{'═'*65}")
        print("  PRICE INDEX HISTORY")
        print(f"{'═'*65}")
        print(f"  {'Cycle':<8} {'Avg Index':>10}  Sparkline")
        print("  " + "─" * 45)
        for (c, idx) in self.price_history:
            bar_len = int((idx - 0.5) * 30)
            bar = "▓" * max(0, bar_len)
            marker = "▲" if idx > 1 else "▼"
            print(f"  {c:<8} {idx:>10.3f}x  {marker} {bar}")

    def print_strategy_usage(self):
        print(f"\n{'═'*65}")
        print("  STRATEGY USAGE SUMMARY")
        print(f"{'═'*65}")
        total = sum(self.strategy_counts.values())
        for name, count in self.strategy_counts.items():
            pct = (count / total * 100) if total else 0
            bar = "█" * int(pct / 3)
            print(f"  {name:<26}  {count:>4}x  ({pct:>4.1f}%)  {bar}")

    def print_event_log(self, n=12):
        print(f"\n{'═'*65}")
        print(f"  LAST {n} PRICING EVENTS")
        print(f"{'═'*65}")
        self.logger.print_recent(n)


# ─────────────────────────────────────────────
# MAIN — run multiple cycles with different configs
# ─────────────────────────────────────────────

def main():
    print("\n" + "╔" + "═"*63 + "╗")
    print("║   DYNAMIC PRICING OPTIMIZATION SYSTEM — OOP Demo          ║")
    print("║   Classes: Product, Strategy, Analyzer, Logger, Engine    ║")
    print("╚" + "═"*63 + "╝")

    engine = PricingEngine()

    scenarios = [
        dict(demand=55, competitor=50, inventory=20, urgency=10, season=90,  label="Low demand, high competition"),
        dict(demand=85, competitor=25, inventory=70, urgency=40, season=120, label="High demand surge season"),
        dict(demand=70, competitor=60, inventory=30, urgency=15, season=100, label="Moderate market"),
        dict(demand=95, competitor=10, inventory=90, urgency=80, season=140, label="Peak event — scarcity spike"),
        dict(demand=40, competitor=80, inventory=10, urgency=5,  season=70,  label="Off-season, price war"),
    ]

    for i, s in enumerate(scenarios):
        label = s.pop("label")
        print(f"\n\n  ▶  Scenario {i+1}: {label}")
        engine.run_cycle(**s)
        time.sleep(0.3)

    engine.print_price_history()
    engine.print_strategy_usage()
    engine.print_event_log(n=15)

    print(f"\n{'═'*65}")
    print("  RUN COMPLETE — all cycles finished.")
    print(f"{'═'*65}\n")


if __name__ == "__main__":
    main()
