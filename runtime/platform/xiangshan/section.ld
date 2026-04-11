pmem_base = 0x80000000;

MEMORY {
  ram (rwxa) : ORIGIN = pmem_base, LENGTH = 1024M
}

ENTRY(_start)

SECTIONS {
  . = ORIGIN(ram);

  .text : {
    *(entry)
    *(.text)
    *(.text.*)
  }
  etext = .;
  _etext = .;

  .rodata : {
    *(.rodata*)
  }

  .data : {
    *(.data)
    *(.data.*)
  }
  edata = .;
  _data = .;

  .bss : {
    _bss_start = .;
    *(.bss*)
    *(.sbss*)
    *(.scommon)
    _bss_end = .;
  }

  _stack_top = ALIGN(0x1000);
  . = _stack_top + 0x40000;
  _stack_pointer = .;

  .tdata : {
    _tdata_begin = .;
    *(.tdata)
    _tdata_end = .;
  }

  .tbss : {
    *(.tbss)
    _tbss_end = .;
  }

  end = .;
  _end = .;
  _heap_start = ALIGN(0x1000);
  _pmem_start = pmem_base;
  _pmem_end = _pmem_start + LENGTH(ram);
}
