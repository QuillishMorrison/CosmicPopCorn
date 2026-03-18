from __future__ import annotations

from dataclasses import dataclass


RESOURCE_KEYS = ["credits", "energy", "fuel", "parts", "data", "crew", "reputation", "alloy", "insight"]
PUBLIC_RESOURCES = ["credits", "energy", "fuel", "parts", "data", "crew", "alloy", "insight"]
SPECIALIZATIONS = ["freight_hub", "repair_nexus", "data_exchange"]


@dataclass(frozen=True)
class ModuleBalance:
    key: str
    name: str
    category: str
    description: str
    build_cost: dict[str, float]
    base_effect: dict[str, float]
    energy_delta: float
    throughput_delta: float
    crew_delta: float = 0


MODULES: dict[str, ModuleBalance] = {
    "dock": ModuleBalance(
        key="dock",
        name="Док",
        category="logistics",
        description="Расширяет поток судов и добавляет больше базовых логистических заказов.",
        build_cost={"credits": 300, "parts": 20, "alloy": 10},
        base_effect={"ship_intake": 3, "contract_slots": 1},
        energy_delta=-2,
        throughput_delta=4,
    ),
    "warehouse": ModuleBalance(
        key="warehouse",
        name="Склад",
        category="storage",
        description="Даёт безопасное хранение и снижает потери от переполнения.",
        build_cost={"credits": 250, "parts": 15, "alloy": 12},
        base_effect={"storage": 100},
        energy_delta=-1,
        throughput_delta=3,
    ),
    "reactor": ModuleBalance(
        key="reactor",
        name="Реактор",
        category="power",
        description="Даёт запас энергии для расширения станции и повышает стабильность цикла.",
        build_cost={"credits": 300, "parts": 16, "alloy": 18},
        base_effect={"energy_supply": 15},
        energy_delta=15,
        throughput_delta=2,
    ),
    "repair_bay": ModuleBalance(
        key="repair_bay",
        name="Ремонтный отсек",
        category="service",
        description="Открывает сервисные заказы и превращает детали в хорошую маржу.",
        build_cost={"credits": 260, "parts": 22, "alloy": 14},
        base_effect={"repair_capacity": 8},
        energy_delta=-3,
        throughput_delta=5,
        crew_delta=-1,
    ),
    "habitat": ModuleBalance(
        key="habitat",
        name="Жилой модуль",
        category="crew",
        description="Стабилизирует экипаж и помогает станции переживать рост нагрузки.",
        build_cost={"credits": 180, "parts": 8, "alloy": 8},
        base_effect={"crew_capacity": 4, "stability": 3},
        energy_delta=-2,
        throughput_delta=1,
        crew_delta=2,
    ),
    "market_terminal": ModuleBalance(
        key="market_terminal",
        name="Рыночный терминал",
        category="trade",
        description="Улучшает цены сделок и открывает больше выгодных NPC-заказов.",
        build_cost={"credits": 220, "parts": 10, "data": 8},
        base_effect={"trade_bonus": 0.08},
        energy_delta=-1,
        throughput_delta=5,
    ),
    "data_core": ModuleBalance(
        key="data_core",
        name="Дата-ядро",
        category="research",
        description="Ускоряет поток данных, инсайта и аналитических заказов.",
        build_cost={"credits": 250, "parts": 12, "data": 18},
        base_effect={"data_output": 8, "insight_gain": 1.1},
        energy_delta=-2,
        throughput_delta=4,
    ),
    "automation_hub": ModuleBalance(
        key="automation_hub",
        name="Узел автоматизации",
        category="automation",
        description="Поздний усилитель всей станции. Дорогой, но очень хорошо масштабирует базу.",
        build_cost={"credits": 420, "parts": 24, "data": 16, "alloy": 16},
        base_effect={"automation": 0.1},
        energy_delta=-3,
        throughput_delta=7,
    ),
}


META_UPGRADES: list[dict[str, object]] = [
    {"key": "boot_efficiency", "name": "Эффективный запуск", "description": "+5% к пропускной способности", "cost": 5, "max_level": 3, "effect_type": "throughput_pct", "effect_value": 0.05},
    {"key": "market_acuity", "name": "Рыночная точность", "description": "+4% к торговой марже", "cost": 6, "max_level": 3, "effect_type": "trade_margin_pct", "effect_value": 0.04},
    {"key": "crew_protocols", "name": "Протоколы экипажа", "description": "+1 к базовому персоналу", "cost": 4, "max_level": 4, "effect_type": "crew_flat", "effect_value": 1.0},
    {"key": "modular_frames", "name": "Модульные каркасы", "description": "-5% к стоимости модулей", "cost": 8, "max_level": 3, "effect_type": "build_discount_pct", "effect_value": 0.05},
    {"key": "salvage_patterns", "name": "Шаблоны утилизации", "description": "+8 деталей за отчёт", "cost": 4, "max_level": 2, "effect_type": "parts_flat", "effect_value": 8.0},
    {"key": "fuel_hedging", "name": "Топливный хедж", "description": "Снижает штраф от волатильности топлива", "cost": 4, "max_level": 3, "effect_type": "fuel_resilience_pct", "effect_value": 0.05},
    {"key": "deep_storage", "name": "Глубокое хранение", "description": "+40 к складу", "cost": 5, "max_level": 3, "effect_type": "storage_flat", "effect_value": 40.0},
    {"key": "clean_grid", "name": "Чистая сеть", "description": "+4 к базовой энергии", "cost": 5, "max_level": 3, "effect_type": "energy_flat", "effect_value": 4.0},
    {"key": "priority_routing", "name": "Приоритетная маршрутизация", "description": "+1 слот контракта", "cost": 7, "max_level": 2, "effect_type": "contract_slots_flat", "effect_value": 1.0},
    {"key": "repair_certification", "name": "Ремонтная сертификация", "description": "+10% к доходу от ремонта", "cost": 7, "max_level": 3, "effect_type": "repair_income_pct", "effect_value": 0.1},
    {"key": "data_caching", "name": "Кэширование данных", "description": "+10% к выпуску данных", "cost": 7, "max_level": 3, "effect_type": "data_output_pct", "effect_value": 0.1},
    {"key": "sector_contacts", "name": "Контакты сектора", "description": "+2 к лимиту репутации", "cost": 5, "max_level": 4, "effect_type": "reputation_flat", "effect_value": 2.0},
    {"key": "efficient_crews", "name": "Слаженные смены", "description": "-5% к нагрузке на персонал", "cost": 6, "max_level": 3, "effect_type": "crew_pressure_pct", "effect_value": 0.05},
    {"key": "guided_ai", "name": "Направляемый ИИ", "description": "+6% к ценности автоматизации", "cost": 8, "max_level": 3, "effect_type": "automation_pct", "effect_value": 0.06},
    {"key": "precision_tools", "name": "Точные инструменты", "description": "+6 к выпуску сплава", "cost": 5, "max_level": 3, "effect_type": "alloy_flat", "effect_value": 6.0},
]


CONTRACT_TEMPLATES: list[dict[str, object]] = [
    {"key": "fuel_shuttle", "title": "Топливный шаттл", "type": "delivery", "resource": "fuel", "quantity": 18, "reward_credits": 210, "reward_reputation": 1},
    {"key": "alloy_batch", "title": "Партия сплава", "type": "delivery", "resource": "alloy", "quantity": 14, "reward_credits": 235, "reward_reputation": 1},
    {"key": "parts_repair", "title": "Латка корпуса", "type": "repair", "resource": "parts", "quantity": 16, "reward_credits": 250, "reward_reputation": 2},
    {"key": "data_dump", "title": "Выгрузка телеметрии", "type": "data", "resource": "data", "quantity": 14, "reward_credits": 225, "reward_reputation": 1},
    {"key": "crew_rotation", "title": "Ротация экипажа", "type": "service", "resource": "crew", "quantity": 4, "reward_credits": 170, "reward_reputation": 1},
    {"key": "vip_dock", "title": "VIP-окно стыковки", "type": "vip", "resource": "fuel", "quantity": 28, "reward_credits": 360, "reward_reputation": 3},
    {"key": "reactor_parts", "title": "Лот реакторных деталей", "type": "delivery", "resource": "parts", "quantity": 22, "reward_credits": 285, "reward_reputation": 2},
    {"key": "station_sync", "title": "Синхронизация данных", "type": "data", "resource": "data", "quantity": 22, "reward_credits": 290, "reward_reputation": 2},
    {"key": "escort_refuel", "title": "Дозаправка эскорта", "type": "delivery", "resource": "fuel", "quantity": 24, "reward_credits": 275, "reward_reputation": 2},
    {"key": "salvage_sort", "title": "Сортировка утиля", "type": "processing", "resource": "alloy", "quantity": 20, "reward_credits": 320, "reward_reputation": 2},
    {"key": "microfracture", "title": "Ремонт микротрещин", "type": "repair", "resource": "parts", "quantity": 24, "reward_credits": 345, "reward_reputation": 2},
    {"key": "science_grant", "title": "Научный грант", "type": "data", "resource": "data", "quantity": 30, "reward_credits": 410, "reward_reputation": 3},
    {"key": "longhaul_supply", "title": "Дальний снабженческий рейс", "type": "supply", "resource": "fuel", "quantity": 36, "reward_credits": 470, "reward_reputation": 3},
    {"key": "vip_repair", "title": "VIP-переоснащение", "type": "vip", "resource": "parts", "quantity": 28, "reward_credits": 490, "reward_reputation": 4},
    {"key": "alloy_exchange", "title": "Обмен сплава", "type": "supply", "resource": "alloy", "quantity": 30, "reward_credits": 440, "reward_reputation": 3},
    {"key": "crew_support", "title": "Поддержка экипажа", "type": "service", "resource": "crew", "quantity": 6, "reward_credits": 240, "reward_reputation": 2},
    {"key": "nav_data", "title": "Навигационные данные", "type": "data", "resource": "data", "quantity": 18, "reward_credits": 235, "reward_reputation": 1},
    {"key": "dock_buffer", "title": "Разгрузка доков", "type": "processing", "resource": "fuel", "quantity": 14, "reward_credits": 195, "reward_reputation": 1},
    {"key": "frontier_repair", "title": "Пограничный ремонт", "type": "repair", "resource": "alloy", "quantity": 22, "reward_credits": 335, "reward_reputation": 2},
    {"key": "relay_refresh", "title": "Обновление реле", "type": "supply", "resource": "parts", "quantity": 28, "reward_credits": 395, "reward_reputation": 3},
]


WORLD_EVENT_TEMPLATES: list[dict[str, object]] = [
    {"key": "fuel_surge", "title": "Всплеск спроса на топливо", "description": "Торговые линии сектора резко подняли потребление топлива.", "market_effects": {"fuel": 1.18}},
    {"key": "fuel_glut", "title": "Переизбыток топлива", "description": "Один из караванов перенасытил рынок поставками.", "market_effects": {"fuel": 0.88}},
    {"key": "parts_shortage", "title": "Дефицит деталей", "description": "Сервисные узлы быстро съедают складские запасы деталей.", "market_effects": {"parts": 1.15}},
    {"key": "parts_relief", "title": "Послабление по деталям", "description": "Сектор получил свежий поток комплектующих.", "market_effects": {"parts": 0.9}},
    {"key": "alloy_rally", "title": "Рост цены сплава", "description": "Производственные линии выкупают сплав быстрее обычного.", "market_effects": {"alloy": 1.12}},
    {"key": "alloy_ease", "title": "Снижение по сплаву", "description": "Рудные караваны стабилизировали поставки сплава.", "market_effects": {"alloy": 0.9}},
    {"key": "data_rush", "title": "Спрос на данные", "description": "Навигационные фирмы подняли закупку аналитики.", "market_effects": {"data": 1.16}},
    {"key": "data_lull", "title": "Затишье на рынке данных", "description": "Спрос на прогнозы временно ослаб.", "market_effects": {"data": 0.9}},
    {"key": "crew_wave", "title": "Волна ротации экипажей", "description": "По всему сектору выросла потребность в персонале.", "market_effects": {"crew": 1.1}},
    {"key": "crew_rest", "title": "Пауза в ротации", "description": "Давление на каналы экипажа стало ниже.", "market_effects": {"crew": 0.93}},
    {"key": "inspection", "title": "Секторная инспекция", "description": "Надёжные станции получают больше выгоды от соответствия нормам.", "market_effects": {"reputation": 1.05}},
    {"key": "scientific_grant", "title": "Научный грант", "description": "Контракты на данные временно оплачиваются выше обычного.", "market_effects": {"data": 1.12, "credits": 1.02}},
    {"key": "vip_flux", "title": "Поток VIP-клиентов", "description": "Премиальные клиенты усилили доходность сервисных линий.", "market_effects": {"fuel": 1.08, "parts": 1.04}},
    {"key": "logistics_storm", "title": "Логистический шторм", "description": "Доковые линии замедлились, и цена быстрой обработки выросла.", "market_effects": {"fuel": 1.05, "parts": 1.06}},
    {"key": "trade_fair", "title": "Торговая ярмарка", "description": "Рыночные спреды временно сузились.", "market_effects": {"credits": 1.03}},
    {"key": "signal_noise", "title": "Шум в каналах связи", "description": "Удерживать целостность данных стало сложнее.", "market_effects": {"data": 1.08}},
    {"key": "escort_arrivals", "title": "Прибытие эскортов", "description": "Ремонтные линии загрузились сопровождающими судами.", "market_effects": {"parts": 1.1, "alloy": 1.08}},
    {"key": "research_window", "title": "Окно исследований", "description": "Прирост инсайта по сектору временно вырос.", "market_effects": {"data": 1.06}},
    {"key": "cold_lane", "title": "Холодный коридор", "description": "Транзит стал ровнее, и потери топлива сократились.", "market_effects": {"fuel": 0.94}},
    {"key": "cargo_bloom", "title": "Грузовой бум", "description": "Рост фрахта усилил движение сплава и топлива.", "market_effects": {"alloy": 1.07, "fuel": 1.03}},
]
