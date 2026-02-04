from otree.api import *
import random
import json

doc = """
Многообъектный аукцион для резервирования путёвок в заповедник "Земля леопарда".
Поддерживает 3 типа аукционов:
1. Uniform Price (Единой цены) - все платят цену отсечения
2. GFP (First Price) - каждый платит свою ставку
3. VCG (Vickrey-Clarke-Groves) - платят внешние эффекты
"""


class C(BaseConstants):
    NAME_IN_URL = 'auction'
    PLAYERS_PER_GROUP = None  # Динамическое число игроков
    NUM_ROUNDS = 3  # Несколько раундов для обучения

    # Типы аукционов
    AUCTION_TYPES = [
        ('uniform', 'Аукцион единой цены (Uniform Price)'),
        ('first_price', 'Аукцион первой цены (GFP)'),
        ('vcg', 'Механизм Викри-Кларка-Гровса (VCG)'),
    ]

    # Параметры по умолчанию
    DEFAULT_ITEMS = 10  # Путёвок на продажу
    DEFAULT_MIN_VALUE = 5000
    DEFAULT_MAX_VALUE = 15000
    DEFAULT_TOUR_COST = 6400  # Себестоимость тура


class Subsession(BaseSubsession):
    auction_type = models.StringField(initial='uniform')
    items_available = models.IntegerField(initial=C.DEFAULT_ITEMS)
    clearing_price = models.IntegerField(initial=0)

    def creating_session(self):
        # Получаем параметры из конфига сессии
        config = self.session.config
        self.auction_type = config.get('auction_type', 'uniform')
        self.items_available = config.get('items_available', C.DEFAULT_ITEMS)

        min_val = config.get('min_valuation', C.DEFAULT_MIN_VALUE)
        max_val = config.get('max_valuation', C.DEFAULT_MAX_VALUE)

        # Присваиваем каждому игроку случайную ценность
        for p in self.get_players():
            p.true_value = random.randint(min_val, max_val)
            # Генерируем индивидуальную функцию спроса
            p.demand_intercept = random.randint(400, 600)
            p.demand_slope = round(random.uniform(-0.03, -0.01), 4)


class Group(BaseGroup):
    total_revenue = models.IntegerField(initial=0)

    def get_sorted_bids(self):
        """Получить отсортированные ставки всех игроков"""
        players = self.get_players()
        bids = []
        for p in players:
            if p.bid_amount and p.bid_amount > 0:
                bids.append({
                    'player': p,
                    'bid': p.bid_amount,
                    'quantity': p.bid_quantity
                })
        return sorted(bids, key=lambda x: x['bid'], reverse=True)

    def calculate_clearing_price(self, bids):
        """Вычислить цену отсечения"""
        items = self.subsession.items_available
        total_quantity = 0
        clearing_price = 0

        for bid_info in bids:
            total_quantity += bid_info['quantity']
            if total_quantity >= items:
                clearing_price = bid_info['bid']
                break

        return clearing_price if clearing_price > 0 else (bids[-1]['bid'] if bids else 0)

    def set_payoffs_uniform(self, bids, clearing_price):
        """Аукцион единой цены - все платят цену отсечения"""
        items_left = self.subsession.items_available

        for bid_info in bids:
            p = bid_info['player']
            if items_left > 0 and bid_info['bid'] >= clearing_price:
                won = min(bid_info['quantity'], items_left)
                p.items_won = won
                p.price_paid = clearing_price * won
                p.is_winner = True
                items_left -= won
            else:
                p.items_won = 0
                p.price_paid = 0
                p.is_winner = False

            # Расчёт прибыли: (цена продажи - себестоимость - цена доступа) * количество
            if p.is_winner:
                profit_per_item = p.true_value - C.DEFAULT_TOUR_COST - clearing_price
                p.payoff = cu(profit_per_item * p.items_won)
            else:
                p.payoff = cu(0)

    def set_payoffs_first_price(self, bids, clearing_price):
        """Аукцион первой цены - каждый платит свою ставку"""
        items_left = self.subsession.items_available

        for bid_info in bids:
            p = bid_info['player']
            if items_left > 0 and bid_info['bid'] >= clearing_price:
                won = min(bid_info['quantity'], items_left)
                p.items_won = won
                p.price_paid = bid_info['bid'] * won  # Платит свою ставку!
                p.is_winner = True
                items_left -= won
            else:
                p.items_won = 0
                p.price_paid = 0
                p.is_winner = False

            if p.is_winner:
                profit_per_item = p.true_value - C.DEFAULT_TOUR_COST - bid_info['bid']
                p.payoff = cu(profit_per_item * p.items_won)
            else:
                p.payoff = cu(0)

    def set_payoffs_vcg(self, bids, clearing_price):
        """VCG механизм - платят внешние эффекты"""
        items_left = self.subsession.items_available

        # Сначала определяем победителей
        winners = []
        for bid_info in bids:
            p = bid_info['player']
            if items_left > 0:
                won = min(bid_info['quantity'], items_left)
                p.items_won = won
                p.is_winner = True
                winners.append(bid_info)
                items_left -= won
            else:
                p.items_won = 0
                p.is_winner = False

        # VCG: каждый победитель платит сумму, равную ставкам тех,
        # кто бы выиграл, если бы победитель не участвовал
        for winner_info in winners:
            winner = winner_info['player']
            # Собираем ставки без этого победителя
            other_bids = [b for b in bids if b['player'] != winner]

            # Что бы получили другие без этого игрока
            items_without = self.subsession.items_available
            externality = 0

            for b in other_bids:
                if items_without > 0:
                    would_win = min(b['quantity'], items_without)
                    items_without -= would_win

            # Цена = ставки вытесненных участников
            items_check = self.subsession.items_available - winner.items_won
            for b in other_bids[items_check:]:
                externality += b['bid'] * min(b['quantity'], winner.items_won)
                break

            winner.price_paid = externality
            profit_per_item = winner.true_value - C.DEFAULT_TOUR_COST
            winner.payoff = cu(profit_per_item * winner.items_won - externality)

        # Проигравшие
        for bid_info in bids:
            p = bid_info['player']
            if not p.is_winner:
                p.price_paid = 0
                p.payoff = cu(0)

    def set_payoffs(self):
        """Основная функция распределения выигрышей"""
        bids = self.get_sorted_bids()

        if not bids:
            return

        clearing_price = self.calculate_clearing_price(bids)
        self.subsession.clearing_price = clearing_price

        auction_type = self.subsession.auction_type

        if auction_type == 'uniform':
            self.set_payoffs_uniform(bids, clearing_price)
        elif auction_type == 'first_price':
            self.set_payoffs_first_price(bids, clearing_price)
        elif auction_type == 'vcg':
            self.set_payoffs_vcg(bids, clearing_price)

        # Считаем общую выручку заповедника
        self.total_revenue = sum(p.price_paid for p in self.get_players())


class Player(BasePlayer):
    # Индивидуальные параметры
    true_value = models.IntegerField(doc="Оценка ценности тура игроком")
    demand_intercept = models.IntegerField(doc="Свободный член функции спроса")
    demand_slope = models.FloatField(doc="Наклон функции спроса")

    # Ставки
    bid_amount = models.IntegerField(
        min=0,
        label="Ваша ставка за одну путёвку (руб.)"
    )
    bid_quantity = models.IntegerField(
        min=1,
        initial=1,
        label="Количество путёвок"
    )

    # Дополнительные заявки (для ступенчатого спроса)
    bid_amount_2 = models.IntegerField(min=0, blank=True, initial=0)
    bid_quantity_2 = models.IntegerField(min=0, blank=True, initial=0)
    bid_amount_3 = models.IntegerField(min=0, blank=True, initial=0)
    bid_quantity_3 = models.IntegerField(min=0, blank=True, initial=0)

    # Результаты
    is_winner = models.BooleanField(initial=False)
    items_won = models.IntegerField(initial=0)
    price_paid = models.IntegerField(initial=0)

    def get_demand_at_price(self, price):
        """Вычислить спрос по цене"""
        q = self.demand_intercept + self.demand_slope * price
        return max(0, int(q))


# PAGES
class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        auction_type = self.subsession.auction_type
        type_names = dict(C.AUCTION_TYPES)
        return dict(
            auction_type=auction_type,
            auction_type_name=type_names.get(auction_type, auction_type),
            items_available=self.subsession.items_available,
            tour_cost=C.DEFAULT_TOUR_COST,
            round_number=self.round_number,
            num_rounds=C.NUM_ROUNDS,
        )


class DemandInfo(Page):
    """Страница с информацией о спросе игрока"""
    def vars_for_template(self):
        # Генерируем точки спроса для отображения
        prices = list(range(8000, 18000, 1000))
        demand_points = []
        for price in prices:
            q = self.get_demand_at_price(price)
            demand_points.append({'price': price, 'quantity': q})

        return dict(
            true_value=self.true_value,
            demand_points=demand_points,
            demand_intercept=self.demand_intercept,
            demand_slope=self.demand_slope,
        )


class Bid(Page):
    form_model = 'player'
    form_fields = ['bid_amount', 'bid_quantity']

    def vars_for_template(self):
        return dict(
            true_value=self.player.true_value,
            items_available=self.subsession.items_available,
            auction_type=self.subsession.auction_type,
            tour_cost=C.DEFAULT_TOUR_COST,
        )

    def error_message(self, values):
        if values['bid_quantity'] > self.subsession.items_available:
            return f"Нельзя запросить больше {self.subsession.items_available} путёвок"


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = 'set_payoffs'
    body_text = "Ожидание других участников аукциона..."


class Results(Page):
    def vars_for_template(self):
        players = self.group.get_players()
        all_bids = sorted(
            [{'id': p.id_in_group, 'bid': p.bid_amount, 'qty': p.bid_quantity,
              'won': p.items_won, 'paid': p.price_paid, 'winner': p.is_winner}
             for p in players],
            key=lambda x: x['bid'],
            reverse=True
        )

        return dict(
            clearing_price=self.subsession.clearing_price,
            items_won=self.player.items_won,
            price_paid=self.player.price_paid,
            is_winner=self.player.is_winner,
            profit=self.player.payoff,
            all_bids=all_bids,
            total_revenue=self.group.total_revenue,
            auction_type=self.subsession.auction_type,
        )


class RoundSummary(Page):
    """Сводка по раунду"""
    def is_displayed(self):
        return True

    def vars_for_template(self):
        # История по раундам
        history = []
        for r in range(1, self.round_number + 1):
            p = self.player.in_round(r)
            history.append({
                'round': r,
                'bid': p.bid_amount,
                'won': p.items_won,
                'paid': p.price_paid,
                'profit': p.payoff,
            })

        total_profit = sum(h['profit'] for h in history)

        return dict(
            history=history,
            total_profit=total_profit,
            is_last_round=self.round_number == C.NUM_ROUNDS,
        )


page_sequence = [
    Introduction,
    DemandInfo,
    Bid,
    ResultsWaitPage,
    Results,
    RoundSummary,
]
