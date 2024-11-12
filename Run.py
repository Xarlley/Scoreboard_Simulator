import time

class Scoreboard:
    def __init__(self):
        self.instructions = []  # 存储指令
        self.cycles = 0         # 当前周期数
        self.reserved = {       # 每个功能单元的占用状态
            'FPU': None,        # 浮点运算单元（FPU）
            'LOAD': None,       # 加载单元
        }
        self.registers = {}     # 寄存器的状态（保存最后写入指令）
        self.pipeline = []      # 每条指令的流水线状态

    def add_instruction(self, instruction):
        self.instructions.append(instruction)
        self.pipeline.append({
            'instruction': instruction,
            'status': 'Issue',    # 初始化状态为“提交”
            'exec_start': None,   # 执行开始时间
            'exec_end': None,     # 执行结束时间
            'write_back': None,   # 回写时间
        })
        
    def print_dynamic_status(self):
        print(f"Cycle {self.cycles}:")
        print(f"{'Instruction':<20} {'Status':<10} {'Exec Start':<12} {'Exec End':<12} {'Write Back':<12}")
        
        for inst in self.pipeline:
            print(f"{inst['instruction']:<20} {inst['status']:<10} {str(inst['exec_start']):<12} {str(inst['exec_end']):<12} {str(inst['write_back']):<12}")
        print("\n")
        
    def simulate_cycle(self):
        for inst in self.pipeline:
            if inst['status'] == 'Issue':
                self.issue(inst)
            elif inst['status'] == 'Execute':
                self.execute(inst)
            elif inst['status'] == 'WriteBack':
                self.write_back(inst)
        
        self.cycles += 1

    def issue(self, inst):
        # 分解指令
        inst_name, dest, src1, src2 = self.parse_instruction(inst['instruction'])
        
        # 检查数据依赖：如果目标寄存器在其他指令中有未完成的写操作，则阻塞发射
        if (self.registers.get(src1) and self.registers[src1]['status'] != 'WriteBack') or \
           (src2 and self.registers.get(src2) and self.registers[src2]['status'] != 'WriteBack'):
            return  # 等待依赖数据完成

        # 检查并分配功能单元
        if inst_name == 'L.D' and self.reserved['LOAD'] is None:
            self.reserved['LOAD'] = inst
            self.registers[dest] = inst
            inst['status'] = 'Execute'
            inst['exec_start'] = self.cycles
            inst['exec_end'] = self.cycles + 1  # 假设加载1周期完成
        elif inst_name in ('MUL.D', 'SUB.D', 'DIV.D', 'ADD.D') and self.reserved['FPU'] is None:
            self.reserved['FPU'] = inst
            self.registers[dest] = inst
            inst['status'] = 'Execute'
            inst['exec_start'] = self.cycles
            inst['exec_end'] = self.cycles + self.execution_cycles(inst_name)  # 根据指令类型确定周期
    
    def execute(self, inst):
        # 只在执行周期结束后，转到写回阶段
        if self.cycles >= inst['exec_end']:
            inst['status'] = 'WriteBack'
            inst['write_back'] = self.cycles
            # 释放功能单元
            inst_name = inst['instruction'].split()[0]
            if inst_name == 'L.D':
                self.reserved['LOAD'] = None
            else:
                self.reserved['FPU'] = None
        
    def write_back(self, inst):
        if inst['write_back'] == self.cycles:
            inst['status'] = 'Completed'
            # 解除寄存器的依赖
            inst_name, dest, _, _ = self.parse_instruction(inst['instruction'])
            if dest in self.registers:
                del self.registers[dest]

    def parse_instruction(self, instruction):
        parts = instruction.replace(",", "").split()
        inst_name = parts[0]
        dest = parts[1]
        src1 = parts[2] if len(parts) > 2 else None
        src2 = parts[3] if len(parts) > 3 else None
        return inst_name, dest, src1, src2

    def execution_cycles(self, inst_name):
        if inst_name == 'MUL.D':
            return 3  # 假设乘法3周期
        elif inst_name == 'SUB.D':
            return 2  # 假设减法2周期
        elif inst_name == 'DIV.D':
            return 5  # 假设除法5周期
        elif inst_name == 'ADD.D':
            return 1  # 假设加法1周期
        return 1  # 默认1周期

def main():
    scoreboard = Scoreboard()

    # 添加指令
    scoreboard.add_instruction("L.D F6,34(R2)")
    scoreboard.add_instruction("L.D F2,45(R3)")
    scoreboard.add_instruction("MUL.D F0,F2,F4")
    scoreboard.add_instruction("SUB.D F8,F2,F6")
    scoreboard.add_instruction("DIV.D F10,F0,F6")
    scoreboard.add_instruction("ADD.D F6,F8,F2")

    # 模拟多个周期
    for _ in range(15):
        scoreboard.simulate_cycle()
        scoreboard.print_dynamic_status()
        time.sleep(0.5)  # 模拟每个周期的延时

if __name__ == "__main__":
    main()
