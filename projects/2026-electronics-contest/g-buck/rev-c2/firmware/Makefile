PREFIX ?= arm-none-eabi-
CC = $(PREFIX)gcc
OBJCOPY = $(PREFIX)objcopy
SIZE = $(PREFIX)size
POWER ?= 0
KEYS ?= 0
LCD ?= 1
BUILD = build/p$(POWER)-k$(KEYS)-l$(LCD)
CFLAGS = -mcpu=cortex-m3 -mthumb -std=c11 -Os -g3 -ffreestanding -fno-builtin -Wall -Wextra -Werror -ffunction-sections -fdata-sections -Iinclude -DPOWER_STAGE_ALLOWED=$(POWER) -DKEYS_ENABLED=$(KEYS) -DLCD_ENABLED=$(LCD)
SRC = $(wildcard src/*.c)
.PHONY: all test clean flash
all: $(BUILD)/gbuck.bin $(BUILD)/gbuck.hex
$(BUILD)/gbuck.elf: $(SRC) $(wildcard include/*.h) stm32f103c8.ld Makefile
	mkdir -p $(BUILD)
	$(CC) $(CFLAGS) $(SRC) -nostdlib -Tstm32f103c8.ld -Wl,--gc-sections,-Map=$(BUILD)/gbuck.map -lgcc -o $@
	$(SIZE) $@
$(BUILD)/gbuck.bin: $(BUILD)/gbuck.elf
	$(OBJCOPY) -O binary $< $@
$(BUILD)/gbuck.hex: $(BUILD)/gbuck.elf
	$(OBJCOPY) -O ihex $< $@
test:
	mkdir -p build/tests
	gcc -std=c11 -Wall -Wextra -Werror -g -fsanitize=address,undefined -Iinclude -DPOWER_STAGE_ALLOWED=1 src/app.c src/measurement.c tests/test_app.c -o build/tests/app
	ASAN_OPTIONS=detect_leaks=0 ./build/tests/app
	gcc -std=c11 -Wall -Wextra -Werror -Iinclude src/app.c src/measurement.c tests/test_locked.c -o build/tests/locked
	./build/tests/locked
flash: all
	openocd -f interface/stlink.cfg -f target/stm32f1x.cfg -c "program $(BUILD)/gbuck.elf verify reset exit"
clean:
	rm -rf build
