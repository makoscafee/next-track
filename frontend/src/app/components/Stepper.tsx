import React from 'react';
import { Check } from 'lucide-react';

interface Step {
  id: number;
  label: string;
  description: string;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
}

export function Stepper({ steps, currentStep }: StepperProps) {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = currentStep > step.id;
          const isCurrent = currentStep === step.id;
          const isUpcoming = currentStep < step.id;

          return (
            <React.Fragment key={step.id}>
              {/* Step Item */}
              <div className="flex flex-col items-center flex-1 relative">
                {/* Circle */}
                <div
                  className={`w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center font-semibold transition-all duration-300 z-10 ${
                    isCompleted
                      ? 'bg-green-500 text-white scale-110'
                      : isCurrent
                      ? 'bg-primary text-primary-foreground scale-110 ring-4 ring-primary/20'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5 md:w-6 md:h-6" />
                  ) : (
                    <span className="text-sm md:text-base">{step.id}</span>
                  )}
                </div>

                {/* Label */}
                <div className="mt-3 text-center">
                  <div
                    className={`text-sm md:text-base font-semibold transition-colors ${
                      isCurrent ? 'text-foreground' : isCompleted ? 'text-green-600' : 'text-muted-foreground'
                    }`}
                  >
                    {step.label}
                  </div>
                  <div
                    className={`text-xs mt-1 hidden md:block transition-colors ${
                      isCurrent ? 'text-muted-foreground' : 'text-muted-foreground/70'
                    }`}
                  >
                    {step.description}
                  </div>
                </div>
              </div>

              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className="flex-1 relative" style={{ marginBottom: '60px' }}>
                  <div className="absolute top-0 left-0 right-0 h-1 bg-muted">
                    <div
                      className={`h-full transition-all duration-500 ${
                        currentStep > step.id ? 'bg-green-500 w-full' : 'bg-muted w-0'
                      }`}
                    />
                  </div>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
