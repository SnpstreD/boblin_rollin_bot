import re
import io
from collections import defaultdict
from typing import Dict, Tuple, List

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def parse_dice_notation(notation: str) -> Tuple[List, int]:
    """ Функция принимает строку с нотацией дайс ролла и возвращает
        распаршенную строку со значениями дайсов и суммой абсолютный модификаторов
    """
    if not notation:
        return [], 0

    dice = []
    flat = 0

    for token in re.findall(r'([+-]?\d*d\d+|[-+]?\d+)', notation.replace(' ', '')):
        if 'd' in token:
            # Обрабатываем знак
            sign = -1 if token.startswith('-') else 1
            clean_token = token.lstrip('+-')
            
            # Парсим количество дайсов и значение
            count_str, faces_str = clean_token.split('d')
            count = int(count_str) if count_str else 1
            faces = int(faces_str)
            
            # Добавляем кубы с учетом знака
            dice.extend([sign * faces] * count)
        else:
            flat += int(token)

    return dice, flat


def calculate_d20_distribution(advantage_status: int = 0) -> Dict[np.int64, np.float64]:
    d20_values = np.arange(1, 21)

    advantage_formulas = {
        -1: lambda x: (41 - 2 * x) / 400,  # Disadvantage
        0: lambda x: np.full(20, 1 / 20),  # No Advantage
        1: lambda x: (2 * x - 1) / 400,  # Advantage
        2: lambda x: (x ** 3 - (x - 1) ** 3) / 8000  # Super Advantage
    }

    probs = advantage_formulas[advantage_status](d20_values)

    return dict(zip(d20_values, probs))


class DiceDistribution:

    def __init__(self,
                 to_hit_roll,
                 damage_roll='',
                 crit_hit_number=20,
                 advantage_status=0,
                 great_weapon_fighting_active=False,
                 halfling_luck_active=False):

        self.to_hit_roll = to_hit_roll.strip()
        self.damage_roll = damage_roll.strip()
        self.crit_hit_number = crit_hit_number
        self.advantage_status = advantage_status
        self.great_weapon_fighting_active = great_weapon_fighting_active
        self.halfling_luck_active = halfling_luck_active

        self.d20_distribution = calculate_d20_distribution(self.advantage_status)
        self.critical_miss_probability = self.d20_distribution[1]

        self.d20_dice_modifiers, self.d20_flat_modifiers = parse_dice_notation(self.to_hit_roll)
        self.damage_dice_modifiers, self.damage_flat_modifiers = parse_dice_notation(self.damage_roll)

    @property
    def critical_hit_probability(self):
        d20_probs = np.array(list(self.d20_distribution.values()))
        crit_mask = np.arange(1, 21) >= self.crit_hit_number
        return np.sum(d20_probs[crit_mask])

    def to_hit_modifiers_distribution(self):
        dice_list, flat_modifiers = self.d20_dice_modifiers, self.d20_flat_modifiers

        # Учитываем отрицательные значения в кубиках
        min_sum = sum(d for d in dice_list if d < 0)
        max_sum = sum(d for d in dice_list if d > 0)

        # Создаем массив вероятностей, охватывающий все возможные суммы
        prob_array = np.zeros(max_sum - min_sum + 1)
        prob_array[-min_sum] = 1.0  # Смещаем нулевую точку

        for dice in dice_list:
            new_prob = np.zeros_like(prob_array)
            dice_abs = abs(dice)
            sign = 1 if dice > 0 else -1

            for val in np.where(prob_array > 0)[0]:
                p = prob_array[val]
                current_sum = val + min_sum  # Переводим в реальную сумму
                # Генерируем все возможные значения для текущего кубика
                for face in range(1, dice_abs + 1):
                    new_val = current_sum + sign * face - min_sum  # Переводим обратно в индекс
                    new_prob[new_val] += p * (1 / dice_abs)
            prob_array = new_prob

        return {k + min_sum + flat_modifiers: v for k, v in enumerate(prob_array) if v > 0}

    @property
    def to_hit_distribution(self):
        d20 = self.d20_distribution
        modifiers = self.to_hit_modifiers_distribution()

        prob_master = defaultdict(float)

        for val_d20, prob_d20 in d20.items():
            if val_d20 == 1 or val_d20 in range(self.crit_hit_number, 21):
                pass
            else:
                for val_modifiers, prob_modifiers in modifiers.items():
                    prob_master[val_d20 + val_modifiers] += prob_d20 * prob_modifiers

        return prob_master
    
    @property
    def damage_distribution(self):
        dice_list, flat_modifiers = self.damage_dice_modifiers, self.damage_flat_modifiers

        def calculate_distribution(dice_list):
            prob_master = defaultdict(float)
            prob_master[0] = 1.0

            for dice in dice_list:
                new_prob_master = defaultdict(float)

                for current_sum, current_prob in prob_master.items():
                    if self.great_weapon_fighting_active:
                        # Создаем распределение для одного кубика с GWF
                        single_die_probs = defaultdict(float)

                        # Стандартные броски
                        for face in range(3, dice + 1):
                            single_die_probs[face] += 1 / dice

                        # Броски с перебросом (1 и 2)
                        for _ in [1, 2]:
                            p_initial = 1 / dice

                            for reroll_face in range(1, dice + 1):
                                single_die_probs[reroll_face] += p_initial * (1 / dice)

                        for face, face_prob in single_die_probs.items():
                            new_prob_master[current_sum + face] += current_prob * face_prob
                    else:
                        # Обычный бросок без GWF
                        for face in range(1, dice + 1):
                            new_prob_master[current_sum + face] += current_prob * (1 / dice)

                prob_master = new_prob_master

            return prob_master

        normal_dist = calculate_distribution(dice_list)
        crit_dist = calculate_distribution(dice_list * 2)

        normal_dist = {k + flat_modifiers: v for k, v in normal_dist.items()}
        crit_dist = {k + flat_modifiers: v for k, v in crit_dist.items()}

        return normal_dist, crit_dist

    def plot_to_hit_distribution(self, save_path=None):
        hit_distribution = self.to_hit_distribution
        
        # Подготовка данных
        values = sorted(hit_distribution.keys())
        probs = np.array([hit_distribution[v] * 100 for v in values])
        
        # Критические значения
        crit_miss_val = min(values) - 1
        crit_hit_val = max(values) + 1
        crit_miss_prob = self.critical_miss_probability * 100
        crit_hit_prob = self.critical_hit_probability * 100
        
        # Объединяем данные
        all_values = [crit_miss_val] + values + [crit_hit_val]
        all_probs = [crit_miss_prob] + list(probs) + [crit_hit_prob]
        
        # Расчет CDF
        reverse_cdf = np.cumsum(all_probs[::-1])[::-1]
        
        # Создаем график
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        fig.subplots_adjust(hspace=0.25)
        
        # Верхний график: распределение
        ax1.bar(values, probs, color='blue', alpha=0.7, label='Normal values', width=0.6)
        ax1.bar([crit_miss_val, crit_hit_val], [crit_miss_prob, crit_hit_prob],
                color='red', alpha=0.7, label='Critical values', width=0.6)
        ax1.set_ylabel('Probability (%)', fontsize=12)
        ax1.set_title('To hit distribution', pad=15, fontsize=14, fontweight='bold')
        ax1.grid(True, linestyle=':', alpha=0.5)
        ax1.legend(fontsize=10, framealpha=0.8)
        
        # Нижний график: CDF
        ax2.plot(all_values, reverse_cdf, 'g-', alpha=0.7, label='P(X ≥ x)', linewidth=1.8)
        ax2.plot(all_values, reverse_cdf, 'go', markersize=5)
        ax2.set_ylabel('CDF (%)', fontsize=12)
        ax2.grid(True, linestyle=':', alpha=0.5)
        ax2.legend(fontsize=10, framealpha=0.8)

        # ОБЩИЕ НАСТРОЙКИ ДЛЯ ОБОИХ ГРАФИКОВ
        x_labels = ['Crit Miss'] + [str(v) for v in values] + ['Crit Hit']

        for ax in [ax1, ax2]:
            # Устанавливаем подписи X
            ax.set_xticks(all_values) 
            ax.set_xticklabels(x_labels, fontsize=10)

            # Поворот подписей для критических значений
            for label in ax.get_xticklabels():
                if label.get_text() in ['Crit Miss', 'Crit Hit']:
                    label.set_rotation(90)
                    label.set_ha('center')
                    label.set_va('top')

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        img_buffer.seek(0)

        return img_buffer

    def plot_damage_distribution(self, damage_type='normal', save_path=None):
        normal_dmg, crit_dmg = self.damage_distribution

        if damage_type == 'normal':
            distribution = normal_dmg
            title = 'Non-critical damage distribution'
        else:
            distribution = crit_dmg
            title = 'Critical damage distribution'

        # Подготовка данных
        values = sorted(distribution.keys())
        probs = np.array([distribution[v] * 100 for v in values])
        
        # Расчет среднего урона
        mean_damage = sum(v * p/100 for v, p in zip(values, probs))
        title = f'{title}\n(average value: {mean_damage:.1f})'
        
        # Расчет CDF
        reverse_cdf = np.cumsum(probs[::-1])[::-1]
        
        # Создаем график
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        fig.subplots_adjust(hspace=0.25)
        
        # Верхний график: распределение
        ax1.bar(values, probs, color='orange', alpha=0.7, width=0.7)
        ax1.set_ylabel('Probability (%)', fontsize=12)
        ax1.set_title(title, pad=15, fontsize=14, fontweight='bold')
        ax1.grid(True, linestyle=':', alpha=0.5)
        
        # Нижний график: CDF
        ax2.plot(values, reverse_cdf, 'r-', alpha=0.7, label='P(X ≥ x)', linewidth=1.8)
        ax2.plot(values, reverse_cdf, 'ro', markersize=4)
        ax2.set_ylabel('CDF (%)', fontsize=12)
        ax2.grid(True, linestyle=':', alpha=0.5)
        ax2.legend(fontsize=10, framealpha=0.8)

        # Умное распределение подписей для избежания наложения
        if len(values) > 15:
            step = max(1, len(values) // 10)
            display_labels = [str(v) if i % step == 0 or i == len(values)-1 else '' 
                              for i, v in enumerate(values)]
        else:
            display_labels = [str(v) for v in values]
        
        for ax in [ax1, ax2]:
            ax.set_xticks(values)
            ax.set_xticklabels(display_labels, fontsize=10)

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        img_buffer.seek(0)
        
        return img_buffer


def main():
    test_roll = DiceDistribution(to_hit_roll='7 + 1d4 - 5 + 1',
                                 damage_roll='2d6 + 2d8 + 10 + 4 + 1',
                                 great_weapon_fighting_active=True,
                                 advantage_status=1)

    test_roll.plot_damage_distribution(damage_type='critical')


if __name__ == '__main__':
    main()
